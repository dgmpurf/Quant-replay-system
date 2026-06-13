# Unified Local Research Workflow Dashboard v0.1

The Unified Local Research Workflow Dashboard is a local-only top-level status report for the research flow from data preparation to current candidates to manual paper trading.

It does not connect to brokers, place orders, automate execution, auto-approve trades, print secrets, or call network APIs.

## Purpose

The project now has separate dashboards and health checks for data preparation, current-candidate artifacts, and paper trading. The unified dashboard answers:

- Has data preparation produced usable artifacts?
- Has snapshot quality run?
- Has a historical backfill dry-run or cache-write run produced reviewable artifact evidence?
- Has a policy-aware reviewed cache export plan produced a reviewable manifest or linked downstream validation?
- Has a current-candidates backfill plan identified warmup/forward-horizon-feasible signal dates?
- Has a current-candidates backfill execution manifest identified which planned signal dates are ready or blocked?
- Has a PIT universe overlay plan produced manual-review rows for point-in-time universe preparation?
- Has a reviewed PIT universe overlay workflow approved rows or identified evidence gaps?
- Has a PIT universe evidence update ingestion run validated reviewer-completed updates into clean review-updates rows?
- Has a PIT evidence checklist validator checked strict stock/ETF evidence completeness before any approval review?
- Has a PIT evidence policy profile comparison shown whether an opt-in EOD/post-close policy would relax only timing/cache-support blockers?
- Has a PIT official status evidence packet consolidated official/source-access context and local EOD support without applying approvals?
- Has a PIT official status evidence packet enrichment merged same-date quotation context and reviewed no-hit support without applying approvals?
- Has reviewer no-hit source coverage acceptance recorded source/query-window/survivorship review context without applying approvals?
- Has an activated replacement worklist produced profile-specific manual evidence update packages?
- Has a reviewed offline market update handoff produced snapshot/current-candidate artifacts?
- Have current candidates been generated?
- Are current-candidate artifacts healthy?
- Has advisory profile calibration produced local threshold-design context?
- Has calibration-to-signal-semantics produced proposal context for future semantics refinement?
- Has signal semantics mapped scores into advisory labels safely?
- Has a signal advisory run produced local alert-preview context?
- Has a single-symbol advisory review been produced for the latest requested symbol?
- Has a question-style single-symbol answer been rendered for the latest requested symbol?
- Has a local conversational advisory question been parsed and routed safely?
- Has a report-only historical replay input gate validator fixture produced validator contract context without becoming real replay input?
- Has the report-only real historical replay input gate validator checked a candidate package or reported that no input package exists?
- Has the report-only minimal replay input package fixture smoke exercised the validator contract without becoming active replay input?
- Has the report-only active replay input promotion workflow produced `PROMOTION_READY_FOR_HUMAN_REVIEW` context without becoming active replay input?
- Has the current-to-paper handoff run?
- Has the paper review template been created and checked?
- Have reviewed decisions, daily paper reports, and reconciliation artifacts been produced?
- Has the paper workflow dashboard run?
- What is the next manual action?

## Workflow Areas

The dashboard scans metadata under:

```text
outputs/reports/historical_backfill/status/
outputs/reports/market_cache_export_policy/status/
outputs/reports/market_cache_export/status/
outputs/reports/data_preparation/workflow_status/
outputs/reports/snapshot_quality/
outputs/reports/market_update_handoff/status/
outputs/reports/current_candidates/
outputs/reports/current_candidates/health/
outputs/reports/current_candidates_backfill_plan/status/
outputs/reports/current_candidates_backfill_execution_manifest/status/
outputs/reports/point_in_time_universe_overlay_plan/status/
outputs/reports/point_in_time_universe_overlay_review/status/
outputs/reports/point_in_time_universe_overlay_export_readiness/status/
outputs/reports/point_in_time_universe_export_staging/status/
outputs/reports/point_in_time_universe_evidence_completion_helper/status/
outputs/reports/point_in_time_universe_evidence_review_worklist/status/
outputs/reports/point_in_time_universe_evidence_update_ingestion/status/
outputs/reports/pit_evidence_checklist_validator/status/
outputs/reports/pit_evidence_policy_profile_comparison/status/
outputs/reports/pit_official_status_evidence_packet/status/
outputs/reports/pit_official_status_evidence_packet_enrichment/status/
outputs/reports/reviewer_no_hit_source_coverage_acceptance/status/
outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1/status/
outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1/status/
outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_v0_1/status/
outputs/reports/manual_diagnostics/minimal_replay_input_package_fixture_smoke_v0_1/status/
outputs/reports/manual_diagnostics/active_replay_input_promotion_v0_1/status/
outputs/reports/universe_profile_policy_audit/status/
outputs/reports/universe_profile_split_worklist_plan/status/
outputs/reports/reviewed_replacement_worklist_plan/status/
outputs/reports/reviewed_replacement_worklist_acceptance/status/
outputs/reports/reviewed_replacement_worklist_activation/status/
outputs/reports/activated_replacement_worklist_evidence_update_plan/status/
outputs/reports/advisory_profile_calibration/status/
outputs/reports/calibration_to_signal_semantics/status/
outputs/reports/signal_semantics/status/
outputs/reports/signals/status/
outputs/reports/single_symbol_advisory/status/
outputs/reports/single_symbol_advisory_answer/status/
outputs/reports/advisory_conversation/status/
outputs/reports/current_to_paper_handoff/
outputs/reports/current_to_paper_review_handoff/
outputs/reports/paper_trading/review_template_health/
outputs/reports/paper_trading/reviews/
outputs/reports/paper_trading/daily/
outputs/reports/paper_trading/reconciliation/
outputs/reports/paper_trading/workflow_status/
```

It reads existing local `metadata.json` or `handoff_metadata.json` files only. It does not rerun any workflow step.

## Historical Backfill Status

`research-status` includes `historical-backfill-status` as a history/cache-building component when those artifacts exist.

The unified summary records the latest backfill id, backfill status/stage, next manual action, task counts, pass/warn/fail/skipped counts, cache-write flag, partial cache-write fields, rejected row counts, rejected symbols/sources, rejected issue categories, and report path. When the backfill stage is `BACKFILL_WARNINGS_NEED_REVIEW`, the dashboard shows the warnings as expected reviewable dry-run warnings rather than live-trading or broker failures.

When an explicit cache-write run accepts some rows and blocks others through protective preflight rejection, the dashboard can show `BACKFILL_PARTIAL_WITH_REJECTIONS`. This is review-required context, not automatic success: rejected rows remain visible and should not be rerun until their comparison/preflight issue is reviewed. If a later reviewed export, snapshot, current-candidates, or paper workflow path has already passed, the partial backfill context does not regress the final dashboard stage.

Historical backfill is earlier than data-pipeline, market-update-handoff, current-candidates, and paper workflow. If later workflow artifacts exist, those later stages take priority for the final `workflow_stage`; historical backfill fields remain visible as context. If historical backfill has active failures and no later valid workflow supersedes it, `research-status` surfaces the failure as actionable.

Cache writes remain explicit and manual. A `WARN` dry-run does not approve cache mutation; review WARN tasks and rerun with `--accept-cache-write` only after manual approval.

## Market Cache Export Plan Status

`research-status` includes `market-cache-export-plan-status` as policy recommendation context when those artifacts exist.

The unified summary records the latest policy plan id, plan status/stage, recommendation counts, source-comparison support counts, generated reviewed manifest path, linked downstream export id, linked downstream snapshot-quality status, and the plan's next manual action. When the plan stage is `SNAPSHOT_READY_FROM_POLICY_PLAN`, the dashboard understands that a policy recommendation plan exists, a reviewed manifest exists, and linked export/snapshot validation may already be ready.

Policy-plan status is earlier than reviewed cache export, current-candidates, market-update-handoff, historical backfill context, and paper workflow in the unified dashboard. If those later artifacts exist, they take priority for the final `workflow_stage`; policy-plan fields remain visible as context. If a policy plan has active failures such as a missing generated manifest or missing explicit source/upstream fields and no later valid workflow supersedes it, `research-status` surfaces the plan failure as actionable.

`PROVISIONAL` recommendations such as ETF/Sina remain visible as reviewable `WARN` signals. If their comparison status is `UNAVAILABLE` because no second ETF reference source exists locally, the dashboard reports the unsupported count as context rather than treating it as a blocking error. A comparison `FAIL` for a recommended stock source remains actionable when the policy plan is the active stage. The policy plan does not export rows, mutate cache, or automatically choose a source for downstream use.

## Market Cache Export Status

`research-status` includes `market-cache-export-status` as the reviewed cache-to-snapshot preparation component when those artifacts exist.

The unified summary records the latest export id, export status/stage, linked pipeline id, linked data-pipeline/data-quality/snapshot-quality statuses, linked snapshot manifest path, and export report path. When the export stage is `SNAPSHOT_READY_FROM_EXPORT`, the dashboard understands that a reviewed cache export has already produced snapshot-ready local data and recommends running `current-candidates` from that snapshot unless a later workflow artifact already exists.

Market-cache-export is earlier than current-candidates, market-update-handoff, and paper workflow. If those later artifacts exist, they take priority for the final `workflow_stage`; cache-export fields remain visible as context. If the latest active cache export has health failures or duplicate-key errors and no later valid workflow supersedes it, `research-status` surfaces the export failure as actionable.

These export fields do not imply automatic source selection. The reviewed cache export remains an explicit source/upstream selection layer, and `data-quality` plus `snapshot-quality` remain required before research use.

## Current-Candidates Backfill Plan Status

`research-status` includes `current-candidates-backfill-plan-status` as multi-date planning context when those artifacts exist.

The unified summary records the latest active warmup-aware plan id, plan status/stage, active health status, selected date count, first and last selected signal dates, warmup trading-day requirement, forward-horizon availability summary, legacy plan counts, active plan issue/error counts, report path, and the plan layer's next manual action. This is plan-only evidence: it does not run `current-candidates`, build snapshot manifests, compute forward-return labels, mutate cache, fetch data, send messages, connect to brokers, or place orders.

When the plan reports `CURRENT_CANDIDATES_BACKFILL_PLAN_READY`, the dashboard treats it as visible non-blocking planning context. Older pre-warmup plan artifacts can remain visible through legacy counts without overriding the active warmup-aware plan. When the active plan reports `CURRENT_CANDIDATES_BACKFILL_PLAN_HEALTH_WARN`, the warning remains reviewable before any future candidate-generation execution. If the active plan reports `CURRENT_CANDIDATES_BACKFILL_PLAN_FAILED` and no later valid workflow supersedes it, the failure is actionable.

Current-candidates backfill plans are earlier than generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to backfill planning; plan fields remain visible for audit. A plan does not imply that candidate artifacts have been generated.

## Current-Candidates Backfill Execution Manifest Status

`research-status` includes `current-candidates-backfill-execution-manifest-status` as multi-date candidate execution-readiness context when those artifacts exist.

The unified summary records the latest execution manifest id, linked plan id, manifest status/stage, health status, row count, ready count, blocked count, blocker counts for missing snapshot, snapshot quality, universe `as_of_date`, and plan infeasibility, report path, and the manifest layer's next manual action. This is readiness context only: it does not run `current-candidates`, build snapshot manifests, run `data-pipeline`, compute forward-return labels, mutate cache, fetch data, send messages, connect to brokers, or place orders.

When the manifest reports `CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_BLOCKED`, the dashboard treats it as a planning blocker. It means required inputs are missing or not point-in-time valid for selected signal dates; it does not mean candidate generation failed, because candidate generation was not run. `BLOCKED_UNIVERSE_AS_OF` specifically means the available universe artifact is later than the signal date and must be replaced or reviewed before any future execution step.

When the manifest reports `CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_READY_FOR_REVIEW`, the dashboard treats the ready rows as human-review planning context. It still does not imply automatic candidate generation or trading approval. Health failures remain actionable when this layer is active.

Current-candidates backfill execution manifests are earlier than generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to execution-manifest readiness; manifest fields remain visible for audit. A manifest does not imply that candidate artifacts have been generated.

## PIT Universe Overlay Plan Status

`research-status` includes `pit-universe-overlay-plan-status` as point-in-time universe preparation context when those artifacts exist.

The unified summary records the latest overlay plan id, plan status/stage, health status, row count, signal date count, symbol count, `NEEDS_MANUAL_REVIEW` count, valid-for-signal-date count, survivorship-bias warning count, report path, and the overlay plan layer's next manual action. This is preparation context only: it does not run `current-candidates`, build snapshot manifests, run `data-pipeline`, compute forward-return labels, mutate cache, fetch data, send messages, connect to brokers, or place orders.

When the status reports `PIT_UNIVERSE_OVERLAY_PLAN_NEEDS_REVIEW`, the dashboard treats the warning as expected reviewable PIT universe preparation work. Generated rows are not point-in-time-valid universe rows yet; `NEEDS_MANUAL_REVIEW` rows must be manually reviewed with evidence before any later snapshot preparation or candidate-generation workflow can use them. Survivorship-bias warnings remain visible so future-universe-derived templates are not mistaken for reviewed point-in-time inputs.

PIT universe overlay plans are earlier than generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to PIT overlay review; overlay fields remain visible for audit. A PIT overlay plan does not imply that current-candidates were generated, snapshots were built, or forward labels were computed.

## PIT Universe Overlay Review Status

`research-status` includes `pit-universe-overlay-review-status` as reviewed PIT universe evidence context when those artifacts exist.

The unified summary records the latest review id, review status/stage, health status, approved count, valid-for-signal-date count, needs-more-evidence count, unresolved survivorship-warning count, report path, and the review layer's next manual action. This is still preparation context only: it does not write usable universe input files, run `current-candidates`, build snapshot manifests, run `data-pipeline`, compute forward-return labels, mutate cache, fetch data, send messages, connect to brokers, or place orders.

When the status reports `PIT_UNIVERSE_OVERLAY_REVIEW_NEEDS_MORE_EVIDENCE`, the dashboard treats the warning as expected reviewable PIT universe preparation work. Unresolved evidence or survivorship-bias issues must be resolved before any later snapshot preparation workflow can consume the rows. When the status reports `PIT_UNIVERSE_OVERLAY_REVIEW_HAS_APPROVED_ROWS` or `PIT_UNIVERSE_OVERLAY_REVIEW_ALL_APPROVED`, approved rows remain evidence artifacts only and do not imply candidate generation has happened.

PIT universe overlay reviews are earlier than generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to review status; review fields remain visible for audit. If review health fails because an approved row lacks reviewer/evidence, has unresolved survivorship risk, or violates local-only safety flags, `research-status` surfaces the failure as actionable when this layer is active.

## PIT Universe Overlay Export Readiness Status

`research-status` includes `pit-universe-overlay-export-readiness-status` as PIT universe export-preparation context when those artifacts exist.

The unified summary records the latest export-readiness id, readiness status/stage, health status, linked review id, approved count, export-ready count, blocked count, no-approved-rows flag, missing required-column count, unresolved survivorship-warning count, report path, and the readiness layer's next manual action. This is report-only context: it does not export usable universe files, write `data/raw`, write `data/processed`, run `current-candidates`, build snapshot manifests, run `data-pipeline`, compute forward labels, mutate cache, fetch data, send messages, connect to brokers, or place orders.

When the status reports `PIT_UNIVERSE_EXPORT_BLOCKED_NO_APPROVED_ROWS`, the dashboard treats the warning as expected reviewable PIT universe preparation work. It means the reviewed overlay has no rows approved for PIT universe export readiness; it does not mean export failed, because no export was attempted. When the status reports `PIT_UNIVERSE_EXPORT_READY_FOR_DRY_RUN`, export-ready rows remain review context for a later explicit export workflow.

PIT universe export readiness is earlier than generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to export readiness; readiness fields remain visible for audit. If readiness health fails because the artifact claims `data/raw` or `data/processed` writes, current-candidates generation, snapshot build, forward labels, unsafe trading flags, or missing required fields on export-ready rows, `research-status` surfaces the failure as actionable when this layer is active.

## PIT Universe Export Staging Status

`research-status` includes `pit-universe-export-staging-status` as guarded PIT universe staging context when those artifacts exist.

The unified summary records the latest staging id, staging status/stage, health status, linked export-readiness id, linked review id, export-ready input count, staged row count, blocked count, diagnostic-source flag, no-ready-row flag, report path, and the staging layer's next manual action. This is staging-only context: it does not write usable universe files, write `data/raw`, write `data/processed`, run `current-candidates`, build snapshot manifests, run `data-pipeline`, compute forward labels, mutate cache, fetch data, send messages, connect to brokers, or place orders.

When the status reports `PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS`, the dashboard treats the warning as expected reviewable PIT universe preparation work. It means no export-ready rows were available for staging; it does not mean a universe export failed, because no export occurred. When the status reports `PIT_UNIVERSE_EXPORT_STAGING_READY_FOR_REVIEW`, staged preview rows remain `outputs/reports` review artifacts only and do not become accepted universe inputs.

PIT universe export staging is earlier than generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to staging; staging fields remain visible for audit. If staging health fails because artifacts claim data writes, current-candidates generation, snapshot build, forward labels, cache mutation, API calls, unsafe trading flags, or incomplete staged universe columns, `research-status` surfaces the failure as actionable when this layer is active.

## PIT Universe Evidence Completion Helper Status

`research-status` includes `pit-universe-evidence-completion-helper-status` as PIT universe evidence-preparation context when those artifacts exist.

The unified summary records the latest helper id, helper status/stage, health status, linked review id, row count, needs-evidence count, rows-with-base-hints count, future-dated hint count, authoritative hint count, report path, and the helper layer's next manual action. This is template-only context: it does not approve rows, set `valid_for_signal_date=true`, export usable universe files, write `data/raw`, write `data/processed`, run `current-candidates`, build snapshot manifests, run `data-pipeline`, compute forward labels, mutate cache, fetch data, send messages, connect to brokers, or place orders.

When the status reports `PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_NEEDS_REVIEW`, the dashboard treats the warning as expected reviewable PIT universe evidence-preparation work. Optional base-universe hints remain non-authoritative; future-dated hints keep survivorship-bias risk visible and cannot approve rows.

PIT universe evidence completion helper artifacts are earlier than generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to helper status; helper fields remain visible for audit. If helper health fails because an artifact claims row approval, `valid_for_signal_date=true`, authoritative hints, data writes, universe export, current-candidates generation, snapshot build, forward labels, unsafe trading flags, API calls, broker access, or message delivery, `research-status` surfaces the failure as actionable when this layer is active.

## PIT Universe Evidence Review Worklist Status

`research-status` includes `pit-universe-evidence-review-worklist-status` as PIT universe evidence-review preparation context when those artifacts exist.

The unified summary records the latest worklist id, worklist status/stage, health status, linked review id, linked helper id, row count, symbol count, signal date count, needs-evidence count, future-dated hint count, report path, and the worklist layer's next manual action. This is worklist-only context: it does not approve rows, set `valid_for_signal_date=true`, export usable universe files, write `data/raw`, write `data/processed`, run `current-candidates`, build snapshot manifests, run `data-pipeline`, compute forward labels, mutate cache, fetch data, send messages, connect to brokers, or place orders.

When the status reports `PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_NEEDS_REVIEW`, the dashboard treats the warning as expected reviewable PIT universe evidence work. Worklist `suggested_*` columns are non-authoritative hints only; future-dated hints remain visible as survivorship-bias context. The update template does not auto-fill `APPROVED_FOR_PIT_UNIVERSE`, `include_flag=true`, or `valid_for_signal_date=true`.

PIT universe evidence review worklists are earlier than generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to worklist status; worklist fields remain visible for audit. If worklist health fails because artifacts approve rows, set valid-for-signal-date flags, claim data writes, current-candidates generation, snapshot build, forward labels, unsafe trading flags, or API calls, `research-status` surfaces the failure as actionable when this layer is active.

## PIT Universe Evidence Update Ingestion Status

`research-status` includes `pit-universe-evidence-update-ingestion-status` as PIT universe evidence-update context when those artifacts exist.

The unified summary records the latest ingestion id, ingestion status/stage, health status, row count, ready-for-review-update count, blocked count, approval-request count, approved-ready count, duplicate identity count, suggested-copy-risk count, report path, clean review-updates path, and the ingestion layer's next manual action. This is ingestion-validation-only context: it does not apply approval, rerun `pit-universe-overlay-review`, export universe files, write `data/raw`, write `data/processed`, run `current-candidates`, build snapshots, compute forward labels, mutate cache, call APIs, send messages, connect to brokers, or place orders.

When the status reports `PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_NO_READY_UPDATES`, the dashboard treats the warning as expected reviewable PIT universe preparation work. It means reviewer updates did not produce any clean rows for a later manual overlay-review run; it does not mean approval failed, because no approval was applied. `PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_PARTIAL_READY` and `PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_READY_FOR_REVIEW_APPLY` still require a separate explicit `pit-universe-overlay-review` run.

PIT universe evidence update ingestion is earlier than generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to ingestion status; ingestion fields remain visible for audit. If ingestion health fails because clean review updates include blocked rows, count consistency breaks, required files are missing, approval is claimed, data writes are claimed, current-candidates were generated, snapshots were built, forward labels were computed, or unsafe trading flags appear, `research-status` surfaces the failure as actionable when this layer is active.

## PIT Evidence Checklist Validator Status

`research-status` includes `pit-evidence-checklist-validator-status` as strict PIT evidence quality-gate context when those artifacts exist.

The unified summary records the latest validator id, validator status/stage, health status, row count, checklist-pass count, blocked count, `stock_core` blocked count, `etf_core` blocked count, report path, and the validator layer's next manual action. This is checklist-validation-only context: it does not apply approval, rerun `pit-universe-overlay-review`, export universe files, write `data/raw`, write `data/processed`, run current-candidates, build snapshots, compute forward labels, mutate cache, call APIs, send messages, connect to brokers, or place orders.

When the status reports `PIT_EVIDENCE_CHECKLIST_VALIDATION_BLOCKED`, the dashboard treats the warning as expected reviewable PIT evidence work. It means strict evidence is still missing or blocked by PIT timing, ST/no-ST, active/not-delisted, survivorship, or source-acceptance checks. It does not mean candidate generation failed, because no candidate generation was run. When the status reports `PIT_EVIDENCE_CHECKLIST_VALIDATION_HAS_APPROVAL_CANDIDATES`, rows are only preview candidates for a later explicit manual review workflow.

PIT evidence checklist validation is earlier than universe profile policy/replacement planning, generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to checklist validation; validator fields remain visible for audit. If validator health fails because files are missing, required columns are missing, approval/export/data-write/current-candidates/snapshot/forward-label/trading safety flags are violated, `research-status` surfaces the failure as actionable when this layer is active.

## PIT Evidence Policy Profile Comparison Status

`research-status` includes `pit-evidence-policy-profile-comparison-status` as PIT evidence policy context when those artifacts exist.

The unified summary records the latest comparison id, comparison status/stage, health status, profile name, row count, strict checklist pass count, EOD low-budget pass count, reviewed no-hit support pass count, no-hit context supported count, reviewer acceptance required count, relaxed blocker count, remaining blocked count, report path, and the comparison layer's next manual action. This is comparison-only context: it does not change the strict validator default, apply approval, run `pit-universe-overlay-review`, run export readiness, run export staging, export universe files, write `data/raw`, write `data/processed`, run current-candidates, build snapshots, compute forward labels, mutate cache, call APIs, send messages, connect to brokers, or place orders.

When the status reports `PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_ALL_BLOCKED`, the dashboard treats the warning as expected reviewable evidence-policy work. It means the opt-in profile did not make any row checklist-pass; remaining non-relaxed PIT evidence gaps still need review. The `EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT` profile can surface no-hit context as reviewer-required support, but that context is not approval evidence and does not resolve survivorship automatically. When the status reports `PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_HAS_CANDIDATE_PREVIEWS`, rows are only manual preview candidates and are not approved.

PIT evidence policy profile comparison is earlier than universe profile policy/replacement planning, generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to profile comparison; comparison fields remain visible for audit. If comparison health fails because strict defaults changed, approval/export/data-write/current-candidates/snapshot/forward-label/trading safety flags are violated, or the profile is not opt-in, `research-status` surfaces the failure as actionable when this layer is active.

## PIT Official Status Evidence Packet Status

`research-status` includes `pit-official-status-evidence-packet-status` as PIT official/source evidence context when those artifacts exist.

The unified summary records the latest packet id, packet status/stage, health status, row count, evidence packet row count, strong official date-specific count, supporting official symbol-level count, supporting local EOD cache count, context-only count, missing evidence count, checklist-pass count, blocked count, EOD low-budget checklist-pass count, report path, and next manual action.

When the status reports `PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_BLOCKED`, the dashboard treats the warning as expected reviewable evidence-acquisition work. It means evidence packets found some context or support but rows still lack complete approval evidence. It does not mean PIT review failed, candidate generation failed, strategy performance failed, or paper workflow failed.

PIT official status evidence packets are earlier than universe profile policy/replacement planning, generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to packet status; packet fields remain visible for audit. If packet health fails because required files/columns are missing or approval/export/data-write/current-candidates/snapshot/forward-label/trading safety flags are violated, `research-status` surfaces the failure as actionable when this layer is active.

## PIT Official Status Evidence Packet Enrichment Status

`research-status` includes `pit-official-status-evidence-packet-enrichment-status` as PIT official evidence enrichment context when those artifacts exist.

The unified summary records the latest enrichment id, enrichment status/stage, health status, source packet id, policy comparison id, row count, strong official same-date quotation count, reviewed no-hit context supported count, reviewer acceptance required count, checklist-pass count, remaining blocked count, report path, and next manual action.

When the status reports `PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_ENRICHMENT_BLOCKED`, the dashboard treats the warning as expected reviewable evidence-preparation work. It means same-date quotation context and reviewed no-hit support have been merged, but rows still require manual acceptance and complete PIT/survivorship evidence. It does not mean PIT review failed, candidate generation failed, strategy performance failed, or paper workflow failed.

PIT official status evidence packet enrichment is earlier than universe profile policy/replacement planning, generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to enrichment status; enrichment fields remain visible for audit. If enrichment health fails because required files/columns are missing, checklist-pass rows appear, or approval/export/data-write/current-candidates/snapshot/forward-label/trading safety flags are violated, `research-status` surfaces the failure as actionable when this layer is active.

## Reviewer No-Hit Source Coverage Acceptance Status

`research-status` includes `reviewer-no-hit-source-coverage-acceptance-status` as PIT evidence-preparation context when those artifacts exist.

The unified summary records the latest acceptance id, acceptance status/stage, health status, linked enrichment id, linked source packet id, linked policy comparison id, row count, accepted supporting-context count, needs-review count, needs-more-evidence count, reviewer-acceptance-required count, survivorship-rationale-required count, checklist-pass count, remaining-blocked count, report path, and next manual action.

When the status reports `REVIEWER_NO_HIT_SOURCE_COVERAGE_ACCEPTANCE_NEEDS_REVIEW`, the dashboard treats the warning as expected reviewable no-hit evidence work. It means no-hit source coverage, query windows, inference limits, and survivorship rationale still require reviewer completion. It does not mean PIT review failed, candidate generation failed, strategy performance failed, or paper workflow failed.

When the status reports `REVIEWER_NO_HIT_SOURCE_COVERAGE_ACCEPTED_AS_SUPPORTING_CONTEXT`, accepted rows are still supporting context only. They do not create `APPROVED_FOR_PIT_UNIVERSE` rows, clean review updates, universe exports, snapshot manifests, current-candidates outputs, or checklist-pass rows by themselves.

Reviewer no-hit source coverage acceptance is earlier than universe profile policy/replacement planning, generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to reviewer acceptance; acceptance fields remain visible for audit. If acceptance health fails because files are missing, accepted rows lack reviewer evidence, approval text appears, or safety flags are violated, `research-status` surfaces the failure as actionable when this layer is active.

## Reviewer No-Hit Acceptance Downstream Impact Status

`research-status` includes `reviewer-no-hit-acceptance-downstream-impact-status` as report-only context when downstream impact artifacts exist.

The unified summary records the latest downstream impact id, status/stage, health status, accepted no-hit context count, packet context gap reduced count, checklist-pass count, remaining-blocked count, approval-applied flag, report path, and next manual action.

When the status reports `REVIEWER_NO_HIT_ACCEPTANCE_DOWNSTREAM_IMPACT_NO_ACCEPTED_CONTEXT`, no reviewer-accepted no-hit context is linked yet. When it reports `REVIEWER_NO_HIT_ACCEPTANCE_DOWNSTREAM_IMPACT_SUPPORTING_CONTEXT_ONLY`, accepted no-hit rows are linked only as supporting context. Neither stage creates `APPROVED_FOR_PIT_UNIVERSE`, clean review updates, universe exports, snapshot manifests, current-candidates outputs, or checklist-pass rows.

Reviewer no-hit acceptance downstream impact is earlier than universe profile policy/replacement planning, generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to downstream impact; impact fields remain visible for audit. If health fails because artifacts claim approval, create review updates, change strict checklist behavior, or violate data-write/current-candidates/snapshot/forward-label/trading safety flags, `research-status` surfaces the failure as actionable when this layer is active.

## First-Batch Reviewer Evidence Completion Plan Status

`research-status` includes `first-batch-reviewer-evidence-completion-plan-status` as report-only manual evidence completion context when those artifacts exist.

The unified summary records the latest completion plan id, status/stage, health status, row count, reviewer completion required count, no-hit acceptance required count, survivorship rationale required count, metadata completion required count, checklist-pass count, remaining-blocked count, clean-review-updates-created flag, approval-applied flag, report path, and next manual action.

When the status reports `FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_NEEDS_REVIEW`, the dashboard treats the warning as expected reviewable evidence-preparation work. It means first-batch reviewer evidence fields are still incomplete. It does not mean PIT review failed, candidate generation failed, strategy performance failed, export failed, or paper workflow failed.

The completion plan keeps every row non-approved. It does not create `APPROVED_FOR_PIT_UNIVERSE`, clean `review_updates.csv`, universe exports, snapshot manifests, current-candidates outputs, or checklist-pass rows. Later paper workflow artifacts keep final workflow priority while first-batch completion fields remain visible for audit.

## First-Batch Partial Completion Impact Status

`research-status` includes `first-batch-partial-completion-impact-status` as report-only reviewer completion impact context when those artifacts exist.

The unified summary records the latest impact id, status/stage, health status, completed row count, completed field count, blocker reduction count, material blocker reduction count, checklist-pass count, remaining-blocked count, clean-review-updates-created flag, approval-applied flag, report path, and next manual action.

When the status reports `FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_NO_COMPLETION`, no partial reviewer fixture has reduced any blocker. When it reports `FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_METADATA_ONLY_REDUCTION`, reviewer metadata was observed, but material PIT evidence blockers remain. These stages are expected planning context; they do not mean PIT review failed, candidate generation failed, export failed, strategy performance failed, or paper workflow failed.

Partial completion impact artifacts keep every row non-approved. They do not create `APPROVED_FOR_PIT_UNIVERSE`, clean `review_updates.csv`, `include_flag=true`, `valid_for_signal_date=true`, universe exports, snapshot manifests, current-candidates outputs, or checklist-pass rows. Later paper workflow artifacts keep final workflow priority while partial completion impact fields remain visible for reviewer planning.

## Material PIT Evidence Gate Closure Plan Status

`research-status` includes `material-pit-evidence-gate-closure-plan-status` as reviewer planning context when material evidence gate closure plan artifacts exist.

The unified summary records the latest plan id, status/stage, health status, row count, checklist-pass candidate count, remaining-blocked count, reusable symbol-level closure count, date-specific closure-required count, reviewer no-hit acceptance-required count, survivorship rationale-required count, metadata closure-required count, stock ST/no-ST required count, clean-review-updates-created flag, approval-applied flag, report path, and next manual action.

When the status reports `MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_NEEDS_EVIDENCE`, material PIT evidence gates remain blocked and reviewer work is still required. When it reports `MATERIAL_PIT_EVIDENCE_GATE_CLOSURE_PLAN_READY_FOR_REVIEWER_FILL`, the plan is ready to guide reviewer fill work, but rows are still not approved and no clean review updates have been created.

Material PIT evidence gate closure plans are report-only. They do not create `APPROVED_FOR_PIT_UNIVERSE`, `include_flag=true`, `valid_for_signal_date=true`, clean `review_updates.csv`, PIT review artifacts, export-readiness artifacts, staging artifacts, universe exports, snapshot manifests, current-candidates outputs, or forward labels. Later paper workflow artifacts keep final workflow priority while material-gate closure plan fields remain visible for reviewer planning.

## Reviewer Material Evidence Fill Guidance Status

`research-status` includes `reviewer-material-evidence-fill-guidance-status` as manual PIT evidence fill guidance context when those artifacts exist.

The unified summary records the latest guidance id, status/stage, health status, row count, reviewer guidance row count, symbol-level guidance count, date-specific guidance count, no-hit acceptance guidance count, survivorship rationale guidance count, metadata guidance count, checklist-pass candidate count, remaining-blocked count, clean-review-updates-created flag, approval-applied flag, report path, and next manual action.

When the status reports `REVIEWER_MATERIAL_EVIDENCE_FILL_GUIDANCE_NEEDS_FILL`, reviewer evidence remains incomplete and the dashboard treats the warning as expected manual evidence-preparation context. It does not imply PIT approval, clean review updates, export-readiness, staging, current-candidates generation, snapshot build, forward labels, or trading readiness.

Reviewer material evidence fill guidance is report-only. Health fails if guidance artifacts contain `APPROVED_FOR_PIT_UNIVERSE`, `include_flag=true`, `valid_for_signal_date=true`, clean `review_updates.csv`, approval-applied flags, data writes, PIT review/export/staging/current-candidates outputs, snapshots, or forward labels. Later paper workflow artifacts keep final workflow priority while reviewer guidance fields remain visible for audit.

## One-Row Material Evidence Fill Package Status

`research-status` includes `one-row-material-evidence-fill-package-status` as one-row PIT evidence fill package context when those artifacts exist.

The unified summary records the latest package id, status/stage, health status, target signal date, target symbol, target universe name, package row count, context-field-drafted count, material-blocker-closed count, checklist-pass candidate count, remaining-blocked count, clean-review-updates-created flag, approval-applied flag, report path, and next manual action.

When the status reports `ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE_CONTEXT_DRAFTED`, context fields were drafted for `2024-04-02 / 000001 / stock_core`, but material PIT blockers remain. This is expected review context and does not imply PIT approval, clean review updates, export-readiness, staging, current-candidates generation, snapshot build, forward labels, or trading readiness.

One-row material evidence fill packages are report-only. Health fails if package artifacts contain `APPROVED_FOR_PIT_UNIVERSE`, `include_flag=true`, `valid_for_signal_date=true`, `survivorship_bias_resolved=true`, clean `review_updates.csv`, approval-applied flags, data writes, PIT review/export/staging/current-candidates outputs, snapshots, or forward labels. Later paper workflow artifacts keep final workflow priority while package fields remain visible for audit.

## One-Row Checklist-Pass Candidate Preview Status

`research-status` includes `one-row-checklist-pass-candidate-preview-status` as one-row PIT checklist-pass preview context when those artifacts exist.

The unified summary records the latest preview id, status/stage, health status, target signal date, target symbol, target universe name, preview row count, reusable-context-field count, strict-requirement-gap count, row-checklist-pass-candidate flag, checklist-pass candidate count, remaining-blocked count, clean-review-updates-created flag, approval-applied flag, report path, and next manual action.

When the status reports `ONE_ROW_CHECKLIST_PASS_CANDIDATE_PREVIEW_CONTEXT_ONLY` or `ONE_ROW_CHECKLIST_PASS_CANDIDATE_PREVIEW_BLOCKED`, the target row remains non-approved and blocked by strict PIT evidence gates. This is expected review context and does not imply PIT approval, clean review update readiness, export-readiness, staging, current-candidates generation, snapshot build, forward labels, or trading readiness.

One-row checklist-pass candidate previews are report-only. Health fails if preview artifacts contain `APPROVED_FOR_PIT_UNIVERSE`, `include_flag=true`, `valid_for_signal_date=true`, `survivorship_bias_resolved=true`, clean `review_updates.csv`, approval-applied flags, data writes, PIT review/export/staging/current-candidates outputs, snapshots, or forward labels. Later paper workflow artifacts keep final workflow priority while preview fields remain visible for audit.

## Historical Replay Input Gate Validator Fixture Status

`research-status` includes `historical-replay-input-gate-validator-fixture-status` as report-only validator contract context when those artifacts exist.

The unified summary records the latest fixture run id, fixture status/stage, health status, case count, blocked case count, pass-candidate case count, active-ready case count, validation issue count, overclaim guard counts, report path, and the fixture layer's next action. It also exports safety flags proving `active_replay_input=false`, `forward_labels_exist=false`, `weights_trained=false`, `active_stock_profile_exists=false`, `real_buy_review_eligible=false`, `validator_implemented=false`, `report_only=true`, `diagnostic_only=true`, no live trading, no broker API, no order placement, no messages, no LLM/API calls, no external API calls, no cache mutation, no current-candidates generation, no snapshot build, and no signal semantics change.

When the status reports `INPUT_GATE_VALIDATOR_FIXTURE_READY`, the dashboard treats it as fixture context only. It is not the real validator, not real replay, and not active replay input. It must not be interpreted as `ACTIVE_REPLAY_INPUT_READY`, `REAL_REPLAY_READY`, `FORWARD_LABEL_READY`, `TRAINING_READY`, `STOCK_PROFILE_READY`, or `REAL_BUY_REVIEW_READY`.

Historical replay input gate validator fixture context is lower priority than later paper workflow, current advisory workflow, and the v1.27 replay substrate schema fixture. If those later or broader artifacts exist, the final `workflow_stage` does not regress to the input-gate fixture; fixture fields remain visible for audit. If fixture health fails, `research-status` surfaces the failure as an artifact repair blocker when this fixture layer is active.

## Historical Replay Input Gate Validator Status

`research-status` includes `historical-replay-input-gate-validator-status` as report-only real validator context when those artifacts exist.

The unified summary records the latest validator run id, validator status/stage, health status, pass-candidate flag, active-replay-ready flag, report path, and next action. It also exports safety flags proving `active_replay_input=false`, `forward_labels_exist=false`, `weights_trained=false`, `active_stock_profile_exists=false`, `real_buy_review_eligible=false`, `report_only=true`, `diagnostic_only=true`, no live trading, no broker API, no order placement, no messages, no LLM/API calls, no external API calls, no cache mutation, no current-candidates generation, no snapshot build, and no signal semantics change.

When the status reports `INPUT_GATE_VALIDATOR_NO_INPUT`, the dashboard treats it as expected report-only validator context: no candidate replay input package was supplied. If a future run reports `INPUT_GATE_VALIDATOR_PASS_CANDIDATE`, that still remains review context only and must not be interpreted as `ACTIVE_REPLAY_INPUT_READY`.

Historical replay input gate validator context is lower priority than later paper workflow and advisory artifacts. If later paper workflow artifacts exist, the final `workflow_stage` remains `PAPER_WORKFLOW_READY`; validator fields remain visible for audit. The validator does not run replay, compute forward labels, train weights, create active stock profiles, create real buy-review eligibility, or validate strategy performance.

## Minimal Replay Input Package Fixture Smoke Status

`research-status` includes `minimal-replay-input-package-fixture-smoke-status` as report-only smoke context when those artifacts exist.

Use `minimal-replay-input-package-fixture-smoke`, `minimal-replay-input-package-fixture-smoke-index`, `minimal-replay-input-package-fixture-smoke-health`, and `minimal-replay-input-package-fixture-smoke-status` to create, discover, safety-check, and summarize this report-only smoke context before it appears in `research-status`.

The unified summary records the latest smoke run id, smoke status, health status, smoke workflow stage, smoke artifact path, input package path, linked validator run id, linked validator status, pass-candidate flag, active-replay-ready flag, report path, and next action. It also exports safety flags proving `active_replay_input=false`, `forward_labels_exist=false`, `weights_trained=false`, `active_stock_profile_exists=false`, `real_buy_review_eligible=false`, `approval_applied=false`, no live trading, no broker API, no order placement, no messages, no LLM/API calls, no external API calls, no cache mutation, no current-candidates generation, no snapshot build, and no signal semantics change.

When the status reports `SMOKE_PASS_CANDIDATE_READY`, the dashboard treats it as validator-contract smoke context only. The linked validator may report `REPLAY_INPUT_GATE_PASS_CANDIDATE`, but that is not active replay input and not `ACTIVE_REPLAY_INPUT_READY`.

Minimal replay input package fixture smoke context is lower priority than later paper workflow and advisory artifacts. If later paper workflow artifacts exist, the final `workflow_stage` remains `PAPER_WORKFLOW_READY`; smoke fields remain visible for audit. The smoke does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not validate strategy performance.

## Active Replay Input Acceptance Status

`research-status` includes `active-replay-input-acceptance-status` as report-only acceptance governance context when those artifacts exist.

Use `active-replay-input-acceptance`, `active-replay-input-acceptance-index`, `active-replay-input-acceptance-health`, and `active-replay-input-acceptance-status` to create, discover, safety-check, and summarize this report-only acceptance context.

The unified summary records the latest acceptance run id, acceptance status, health status, acceptance workflow stage, acceptance artifact path, ready-for-active-ready-review flag, report path, and next action. It also exports safety flags proving `active_replay_input_ready=false`, `active_replay_input=false`, `active_ready_emitted=false`, `forward_labels_exist=false`, `weights_trained=false`, `active_stock_profile_exists=false`, `real_buy_review_eligible=false`, `approval_applied=false`, no live trading, no broker API, no order placement, no messages, no LLM/API calls, no external API calls, no cache mutation, no current-candidates generation, no snapshot build, and no signal semantics change.

When the status reports `ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW`, the dashboard treats it as acceptance governance context only. It is not active replay input and not `ACTIVE_REPLAY_INPUT_READY`. It must not be interpreted as replay permission, active-ready emission, paper approval, buy-review eligibility, or trading authorization.

Active replay input acceptance context is lower priority than later paper workflow and advisory artifacts. If later paper workflow artifacts exist, the final `workflow_stage` remains `PAPER_WORKFLOW_READY`; acceptance fields remain visible for audit. The acceptance workflow does not create active replay input, does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not validate strategy performance.

## Active Replay Input Active-Ready Status

`research-status` includes `active-replay-input-active-ready-status` as report-only active-ready governance context when those artifacts exist.

Use `active-replay-input-active-ready`, `active-replay-input-active-ready-index`, `active-replay-input-active-ready-health`, and `active-replay-input-active-ready-status` to create, discover, safety-check, and summarize this report-only active-ready context.

The unified summary records the latest active-ready run id, active-ready status, health status, active-ready workflow stage, active-ready artifact path, ready-for-final-review flag, report path, and next action. It also exports safety flags proving `active_replay_input_ready=false`, `active_replay_input=false`, `active_ready_emitted=false`, `forward_labels_exist=false`, `weights_trained=false`, `active_stock_profile_exists=false`, `real_buy_review_eligible=false`, `approval_applied=false`, no live trading, no broker API, no order placement, no messages, no LLM/API calls, no external API calls, no cache mutation, no `data/raw`, no `data/processed`, no `data/cache`, no current-candidates generation, no snapshot build, and no signal semantics change.

When the status reports `ACTIVE_READY_READY_FOR_FINAL_REVIEW`, the dashboard treats it as active-ready final-review context only. It is not active replay input and not `ACTIVE_REPLAY_INPUT_READY`. It must not be interpreted as replay permission, active-ready emission, paper approval, buy-review eligibility, performance validation, or trading authorization.

Active replay input active-ready context is lower priority than later paper workflow and advisory artifacts. If later paper workflow artifacts exist, the final `workflow_stage` remains `PAPER_WORKFLOW_READY`; active-ready fields remain visible for audit. The active-ready workflow does not create active replay input, does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, does not authorize trading, and does not validate strategy performance.

## Active Replay Input Final-Review Status

`research-status` includes `active-replay-input-final-review-status` as report-only final-review emission-readiness governance context when those artifacts exist.

Use `active-replay-input-final-review`, `active-replay-input-final-review-index`, `active-replay-input-final-review-health`, and `active-replay-input-final-review-status` to create, discover, safety-check, and summarize this report-only final-review context.

The unified summary records the latest final-review run id, final-review status, health status, final-review workflow stage, final-review artifact path, ready-for-emission-review flag, report path, and next action. It also exports safety flags proving `active_replay_input_ready=false`, `active_replay_input=false`, `active_ready_emitted=false`, `forward_labels_exist=false`, `weights_trained=false`, `active_stock_profile_exists=false`, `real_buy_review_eligible=false`, `approval_applied=false`, no live trading, no broker API, no order placement, no messages, no LLM/API calls, no external API calls, no cache mutation, no `data/raw`, no `data/processed`, no `data/cache`, no current-candidates generation, no snapshot build, and no signal semantics change.

When the status reports `FINAL_REVIEW_READY_FOR_EMISSION_REVIEW`, the dashboard treats it as final-review emission-readiness context only. It is not active replay input and not `ACTIVE_REPLAY_INPUT_READY`. It must not be interpreted as replay permission, active-ready emission, paper approval, buy-review eligibility, performance validation, or trading authorization.

Active replay input final-review context is lower priority than later paper workflow and advisory artifacts. If later paper workflow artifacts exist, the final `workflow_stage` remains `PAPER_WORKFLOW_READY`; final-review fields remain visible for audit. The final-review workflow does not create active replay input, does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, does not authorize trading, and does not validate strategy performance.

## Active Replay Input Emission Status

`research-status` includes `active-replay-input-emission-status` as report-only emission governance context when those artifacts exist.

Use `active-replay-input-emission`, `active-replay-input-emission-index`, `active-replay-input-emission-health`, and `active-replay-input-emission-status` to create, discover, safety-check, and summarize this report-only emission context.

The unified summary records the latest emission run id, emission status, health status, emission workflow stage, emission artifact path, ready-for-active-ready-review flag, report path, and next action. It also exports safety flags proving `active_replay_input_ready=false`, `active_replay_input=false`, `active_ready_emitted=false`, `replay_execution_allowed=false`, `forward_labels_allowed=false`, `training_allowed=false`, `stock_profile_allowed=false`, `buy_review_allowed=false`, `trading_allowed=false`, `forward_labels_exist=false`, `weights_trained=false`, `active_stock_profile_exists=false`, `real_buy_review_eligible=false`, `approval_applied=false`, no live trading, no broker API, no order placement, no messages, no LLM/API calls, no external API calls, no cache mutation, no `data/raw`, no `data/processed`, no `data/cache`, no current-candidates generation, no snapshot build, and no signal semantics change.

When the status reports `EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW`, the dashboard treats it as emission review context only. It is not active replay input and not `ACTIVE_REPLAY_INPUT_READY`. It must not be interpreted as replay permission, active-ready emission, paper approval, buy-review eligibility, performance validation, or trading authorization.

Active replay input emission context is lower priority than later paper workflow and advisory artifacts. If later paper workflow artifacts exist, the final `workflow_stage` remains `PAPER_WORKFLOW_READY`; emission fields remain visible for audit. The emission workflow does not emit `ACTIVE_REPLAY_INPUT_READY`, does not create active replay input, does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, does not authorize trading, and does not validate strategy performance.

## Universe Profile Policy Audit Status

`research-status` includes `universe-profile-policy-audit-status` as universe naming and split-policy context when those artifacts exist.

The unified summary records the latest audit id, audit status/stage, health status, row count, stock/ETF/mixed counts, ambiguous-policy count, recommended `stock_core`, `etf_core`, and `mixed_demo_core` counts, report path, and the audit layer's next manual action. This is policy-audit-only context: it does not approve rows, reject rows, export universe files, write `data/raw`, write `data/processed`, run `current-candidates`, build snapshots, compute forward labels, mutate cache, call APIs, send messages, connect to brokers, or place orders.

When the status reports `UNIVERSE_PROFILE_POLICY_AMBIGUOUS_MIXED_UNIVERSE`, the dashboard treats the warning as expected reviewable policy context. It means the current artifact contains mixed STOCK/ETF rows under a universe label such as `etf_core`; it does not approve or reject any PIT universe row.

Universe profile policy audits are earlier than generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to policy audit status; policy fields remain visible for audit. If audit health fails because an artifact claims approval, rejection, data writes, current-candidates generation, snapshot build, forward labels, cache mutation, network/API use, unsafe trading flags, broker access, order placement, or message delivery, `research-status` surfaces the failure as actionable when this layer is active.

## Universe Profile Split-Worklist Plan Status

`research-status` includes `universe-profile-split-worklist-plan-status` as future worklist split-planning context when those artifacts exist.

The unified summary records the latest split-worklist plan id, plan status/stage, health status, row count, STOCK/ETF/legacy mixed-demo counts, recommended `stock_core`, `etf_core`, and `mixed_demo_core` counts, profile-conflict count, report path, and the plan layer's next manual action. This is split-planning-only context: it does not approve rows, reject rows, mutate active worklists, export universe files, write `data/raw`, write `data/processed`, run `current-candidates`, build snapshots, compute forward labels, mutate cache, call APIs, send messages, connect to brokers, or place orders.

When the status reports `UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_HAS_PROFILE_CONFLICTS`, the dashboard treats the warning as expected reviewable split-planning context. It means the current legacy source rows have a universe-label/instrument-type mismatch under the clarified profile registry; it does not apply any approval, rejection, or replacement worklist.

Universe profile split-worklist plans are earlier than generated replacement worklists, current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to split-plan status; split-plan fields remain visible for audit. If plan health fails because an artifact claims active worklist mutation, approval, rejection, data writes, universe export, current-candidates generation, snapshot build, forward labels, cache mutation, network/API use, unsafe trading flags, broker access, order placement, or message delivery, `research-status` surfaces the failure as actionable when this layer is active.

## Reviewed Replacement Worklist Plan Status

`research-status` includes `reviewed-replacement-worklist-plan-status` as future replacement-worklist planning context when those artifacts exist.

The unified summary records the latest replacement plan id, plan status/stage, health status, source split plan id, total row count, `stock_core`, `etf_core`, and `mixed_demo_core` row counts, profile-conflict count, active-worklist mutation flag, report path, and the plan layer's next manual action. This is replacement-template-only context: it does not approve rows, reject rows, mutate active worklists, export universe files, write `data/raw`, write `data/processed`, run `current-candidates`, build snapshots, compute forward labels, mutate cache, call APIs, send messages, connect to brokers, or place orders.

When the status reports `REVIEWED_REPLACEMENT_WORKLIST_PLAN_READY`, the dashboard treats it as non-blocking planning context. It means future replacement templates are ready for manual review; it does not mean replacement worklists have been activated or used.

Reviewed replacement worklist plans are earlier than generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to replacement-plan status; replacement-plan fields remain visible for audit. If health fails because an artifact claims active worklist mutation, approval, rejection, data writes, universe export, current-candidates generation, snapshot build, forward labels, cache mutation, network/API use, unsafe trading flags, broker access, order placement, or message delivery, `research-status` surfaces the failure as actionable when this layer is active.

## Reviewed Replacement Worklist Acceptance Status

`research-status` includes `reviewed-replacement-worklist-acceptance-status` as report-only replacement-template acceptance context when those artifacts exist.

The unified summary records the latest acceptance id, acceptance status/stage, health status, replacement plan id, lineage ids, total row count, `stock_core`, `etf_core`, and `mixed_demo_core` row counts, profile-conflict count, acceptance acknowledgement flag, active-worklist mutation flag, report path, and the acceptance layer's next manual action.

Acceptance means the replacement templates were acknowledged as planning artifacts only. It does not activate replacement worklists, approve or reject PIT rows, export universe files, generate candidates, build snapshots, compute labels, or validate strategy performance.

Reviewed replacement worklist acceptance is earlier than generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to acceptance status; acceptance fields remain visible for audit. If health fails because an artifact claims active worklist mutation, approval, rejection, data writes, universe export, current-candidates generation, snapshot build, forward labels, cache mutation, network/API use, unsafe trading flags, broker access, order placement, or message delivery, `research-status` surfaces the failure as actionable when this layer is active.

## Reviewed Replacement Worklist Activation Status

`research-status` includes `reviewed-replacement-worklist-activation-status` as report-only activated replacement-template planning context when those artifacts exist.

The unified summary records the latest activation id, activation status/stage, health status, replacement plan id, lineage ids, total row count, `stock_core`, `etf_core`, and `mixed_demo_core` row counts, profile-conflict count, activation acknowledgement flag, active-worklist mutation flag, report path, and the activation layer's next manual action.

Activation means the accepted replacement templates were acknowledged as the active planning context only. It does not replace active worklists, approve or reject PIT rows, export universe files, generate candidates, build snapshots, compute labels, or validate strategy performance.

Reviewed replacement worklist activation is earlier than generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to activation status; activation fields remain visible for audit. If health fails because an artifact claims active worklist mutation, approval, rejection, data writes, universe export, current-candidates generation, snapshot build, forward labels, cache mutation, network/API use, unsafe trading flags, broker access, order placement, or message delivery, `research-status` surfaces the failure as actionable when this layer is active.

## Activated Replacement Worklist Evidence Update Plan Status

`research-status` includes `activated-replacement-worklist-evidence-update-plan-status` as profile-specific manual evidence collection planning context when those artifacts exist.

The unified summary records the latest evidence-update plan id, plan status/stage, health status, activation id, replacement plan id, source worklist id, total row count, `stock_core`, `etf_core`, and `mixed_demo_core` row counts, approved/rejected counts, valid-for-signal-date count, clean-review-updates flag, active-worklist mutation flag, report path, and the plan layer's next manual action.

Evidence update plans use activated replacement templates as planning context only. They create profile-specific worklists, update templates, first-batch packages, and an evidence source checklist. They do not create clean review updates, approve or reject PIT rows, export universe files, replace active worklists, generate candidates, build snapshots, compute labels, or validate strategy performance.

Activated replacement evidence update plans are earlier than generated current-candidates, advisory layers, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to evidence-update planning; evidence package fields remain visible for audit. If health fails because an artifact claims approval, rejection, clean review updates, active worklist mutation, data writes, universe export, current-candidates generation, snapshot build, forward labels, cache mutation, network/API use, unsafe trading flags, broker access, order placement, or message delivery, `research-status` surfaces the failure as actionable when this layer is active.

## Advisory Profile Calibration Status

`research-status` includes `advisory-profile-calibration-status` as threshold-design context when calibration artifacts exist.

The unified summary records the latest calibration run id, calibration status/stage, profile, health status, simulated action counts, issue count, report path, and the calibration layer's next manual action. Calibration labels are local design outputs only. `REVIEW_BUY_CANDIDATE` means a human-review candidate for threshold analysis, not an order, paper approval, broker instruction, or automatic execution.

When calibration reports `DEMO_ADVISORY_PROFILE_CALIBRATION_VALIDATED`, the dashboard treats the warning as expected demo context. Demo calibration remains `DEMO_ONLY` and does not become real BUY/SELL guidance. When calibration reports `ADVISORY_PROFILE_CALIBRATION_READY_FOR_REVIEW`, review labels remain visible as manual review context, with auto-order disabled.

Advisory profile calibration is earlier than signal semantics, signal advisory, single-symbol advisory, advisory conversation, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to calibration; calibration fields remain visible for audit. If calibration health fails because safety boundaries are broken, such as `auto_order_allowed=true`, missing no-live/no-broker/no-message metadata, `APPROVED_FOR_PAPER`, message-delivery metadata, missing required files, or demo BUY/SELL leakage, `research-status` surfaces the failure as actionable when calibration is the active stage.

## Calibration-to-Signal Semantics Status

`research-status` includes `calibration-to-signal-semantics-status` as proposal/design context when proposal artifacts exist.

The unified summary records the latest proposal run id, proposal status/stage, health status, `defaults_changed`, proposal categories, calibration run count, observed review-buy/watch/blocked counts, report path, and the proposal layer's next manual action. This context is not strategy validation and does not change `signal_semantics` defaults.

When the status reports `CALIBRATION_TO_SEMANTICS_NEEDS_MORE_EVIDENCE`, the dashboard treats the warning as expected reviewable design context. The next action remains conservative: keep current defaults, consider `WATCH` expansion only after more evidence, and do not expand BUY review yet. When the status reports `CALIBRATION_TO_SEMANTICS_PROPOSAL_READY`, the proposal remains manual design context only.

`defaults_changed=true` is actionable and unsafe for this proposal-only layer because the tool must not mutate config or executable semantics thresholds. Health failures also remain actionable when this layer is active.

Calibration-to-signal-semantics proposals are earlier than current-candidates, signal semantics, signal advisory, single-symbol advisory, advisory conversation, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to proposal status; proposal fields remain visible for audit.

## Signal Semantics Status

`research-status` includes `signal-semantics-status` as advisory-policy context when semantics artifacts exist.

The unified summary records the latest semantics run id, semantics status/stage, health status, action counts, issue count, profile, input path, report path, and the semantics layer's next manual action. Semantics labels are local advisory-policy labels only. `REVIEW_BUY_CANDIDATE` means human review candidate, not an order, paper approval, broker instruction, or automatic execution.

When signal semantics reports `DEMO_SIGNAL_SEMANTICS_VALIDATED`, the dashboard treats the warning as expected demo context. Demo semantics remain `DEMO_ONLY` and do not become real BUY/SELL guidance. When signal semantics reports `SIGNAL_SEMANTICS_READY_FOR_REVIEW`, review labels remain visible as manual review context, with auto-order disabled.

Signal semantics is earlier than signal advisory, single-symbol advisory, advisory conversation, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to signal semantics; semantics fields remain visible for audit. If semantics health fails because safety boundaries are broken, such as `auto_order_allowed=true`, missing no-live/no-broker metadata, `APPROVED_FOR_PAPER`, message-delivery metadata, missing required files, or demo BUY/SELL leakage, `research-status` surfaces the failure as actionable when semantics is the active stage.

## Shared Semantics Provenance

`research-status` also exposes shared signal semantics provenance from downstream advisory status views. The summary CSV, metadata, markdown report, and CLI output include provenance context for signal advisory, single-symbol advisory, question-style single-symbol answers, and advisory conversation artifacts:

- `signal_advisory_semantics_policy_source`
- `signal_advisory_semantics_policy_version`
- `single_symbol_advisory_semantics_policy_source`
- `single_symbol_advisory_answer_semantics_policy_source`
- `advisory_conversation_semantics_policy_source`
- `latest_semantics_action`
- `semantics_provenance_present`
- `semantics_provenance_missing_legacy_count`

These fields are audit metadata only. They show which shared classifier produced or informed the latest advisory label; they do not approve trading, paper execution, broker access, message delivery, or automatic order placement.

Legacy artifacts that predate provenance remain readable. Missing legacy provenance is visible through the `*_semantics_missing_provenance_legacy_warning_only` fields and the aggregate missing count, but it does not override a later valid paper workflow. Unsafe provenance detected by health checks, such as semantics auto-order being allowed or a mismatched semantics policy source, remains actionable when that advisory layer is the active stage.

## Signal Advisory Status

`research-status` includes `signal-advisory-status` as advisory context when signal artifacts exist.

The unified summary records the latest signal run id, advisory status/stage, signal health status, signal count, demo signal count, advisory action counts, alert preview path, source current-candidate run id, selection profile, demo mode, and `not_strategy_recommendation` flag. The alert preview remains local markdown only; the dashboard does not send SMS, email, Telegram, WeChat, webhooks, or broker instructions.

When signal advisory reports `DEMO_SIGNAL_ADVISORY_VALIDATED`, the dashboard treats the warning as expected demo context. `DEMO_ONLY` remains visible, does not become BUY/SELL guidance, and still requires manual review of the local alert preview. If no later workflow exists, the final stage can be `DEMO_SIGNAL_ADVISORY_VALIDATED` or `SIGNAL_ADVISORY_READY_FOR_REVIEW`.

Signal advisory is earlier than market-update handoff and paper workflow. If later paper workflow artifacts exist, those later stages take priority for the final `workflow_stage`; signal advisory fields remain visible as context. If signal health fails because advisory safety fields are unsafe, such as `auto_order_allowed=true`, missing manual confirmation, missing no-live-trading metadata, or message-delivery metadata, `research-status` surfaces the failure as actionable when signal advisory is the active stage.

## Single-Symbol Advisory Status

`research-status` includes `single-symbol-advisory-status` as one-symbol advisory context when review artifacts exist.

The unified summary records the latest advisory run id, latest symbol, advisory status/stage/action, health status, final score, demo flags, alert preview path, and the single-symbol review's next manual action. The alert preview remains local markdown only; the dashboard does not send messages, place orders, connect to brokers, or treat the review as execution approval.

When the latest review reports `DEMO_SINGLE_SYMBOL_ADVISORY_VALIDATED`, the dashboard treats the warning as expected demo context. `DEMO_ONLY` remains visible and does not become BUY/SELL guidance. When the latest review reports `SINGLE_SYMBOL_ADVISORY_NOT_FOUND`, the dashboard treats it as safe reviewable context as long as no recommendation was invented.

Single-symbol advisory is context below broader workflow stages such as reviewed cache export, current-candidates, signal advisory, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to the one-symbol review; the single-symbol fields remain visible for audit. If single-symbol advisory health fails because safety fields are unsafe, such as `auto_order_allowed=true`, missing no-live-trading/no-broker/no-message-sent metadata, demo BUY/SELL leakage, or `NOT_FOUND` with invented advice, `research-status` surfaces the failure as actionable when single-symbol advisory is the active stage.

## Single-Symbol Advisory Answer Status

`research-status` includes `single-symbol-advisory-answer-status` as question-style advisory context when deterministic answer artifacts exist.

The unified summary records the latest answer run id, latest symbol, answer status/stage/action, health status, question, answer style, demo flags, markdown answer path, and the answer layer's next manual action. The answer markdown is local only; the dashboard does not call an LLM, send messages, place orders, connect to brokers, or treat the answer as execution approval.

When the latest answer reports `DEMO_SINGLE_SYMBOL_ADVISORY_ANSWER_VALIDATED`, the dashboard treats the warning as expected demo context. `DEMO_ONLY` remains visible and does not become BUY/SELL guidance. When the latest answer reports `SINGLE_SYMBOL_ADVISORY_ANSWER_NOT_FOUND`, the dashboard treats it as safe reviewable context as long as no recommendation was invented.

Question-style answers are context below broader workflow stages such as single-symbol advisory, signal advisory, current-candidates, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to the answer layer; answer fields remain visible for audit. If answer health fails because safety fields are unsafe, such as `auto_order_allowed=true`, missing no-live-trading/no-broker/no-message-sent metadata, `llm_api_called=true`, demo BUY/SELL wording leakage, or `NOT_FOUND` with invented advice, `research-status` surfaces the failure as actionable when the answer layer is the active stage.

## Advisory Conversation Status

`research-status` includes `advisory-conversation-status` as local conversational advisory context when deterministic conversation artifacts exist.

The unified summary records the latest conversation run id, original question, parsed symbol, parsed intent, conversation status/stage/action, health status, parser type, `llm_api_called`, `no_message_sent`, no-live/no-broker/auto-order flags, linked answer markdown path, and the conversation layer's next manual action. This is local deterministic routing only; the dashboard does not call an LLM or external API, send messages, place orders, connect to brokers, or treat the parsed intent as execution approval.

When the latest conversation reports `DEMO_ADVISORY_CONVERSATION_VALIDATED`, the dashboard treats the warning as expected demo context. `DEMO_ONLY` remains visible and does not become BUY/SELL guidance. When the latest conversation reports `ADVISORY_CONVERSATION_NOT_FOUND` or `ADVISORY_CONVERSATION_PARSE_FAILED`, the dashboard treats it as safe reviewable context as long as no symbol or recommendation was invented.

Advisory conversation is context below broader workflow stages such as question-style answer status, single-symbol advisory, signal advisory, current-candidates, market-update handoff, and paper workflow. If those later artifacts exist, the final `workflow_stage` does not regress to the conversation layer; conversation fields remain visible for audit. If conversation health fails because safety fields are unsafe, such as `llm_api_called=true`, `no_message_sent=false`, missing no-live/no-broker metadata, `auto_order_allowed=true`, demo BUY/SELL leakage, or `PARSE_FAILED` / `NOT_FOUND` with invented advice, `research-status` surfaces the failure as actionable when the conversation layer is the active stage.

## Active Snapshot Linkage

`research-status` follows snapshot-quality evidence through the active workflow chain before falling back to standalone snapshot-quality artifacts. The priority order is:

```text
paper workflow
-> current-candidates
-> market-update-handoff
-> market-cache-export
-> market-cache-export-plan
-> standalone snapshot-quality
```

When an active linked chain reports `snapshot_quality_status=PASS`, older standalone `SNAPSHOT_QUALITY` warnings remain visible as context but do not force the final stage to `LOCAL_RESEARCH_NEEDS_ATTENTION`. If the active linked snapshot is `WARN`, the warning remains actionable. If it is `FAIL`, the dashboard records an active snapshot error and blocks progress.

The summary CSV and metadata include `linked_snapshot_quality_status`, `active_snapshot_chain`, `active_snapshot_warning_count`, `active_snapshot_error_count`, `stale_snapshot_warning_count`, and `unrelated_snapshot_warning_count` so downstream dashboards can tell active snapshot problems from stale or unrelated local artifact warnings.

## Market Update Handoff Status

`research-status` includes `market-update-handoff-status` as a pre-paper workflow component when those artifacts exist.

The unified summary records the latest handoff id, handoff status/stage, linked pipeline id, linked snapshot-quality status, linked current-candidate run id, and the handoff's next manual action. When the handoff stage is `CURRENT_CANDIDATES_READY_FOR_PAPER_SMOKE_TEST`, the dashboard treats current candidates as ready for a local paper workflow smoke test and recommends `current-to-paper`.

If a handoff is `WARN` only because provisional rows such as AKShare/Sina ETF `WARN_ACCEPT` rows were included, the warning remains visible but is classified as non-blocking for the active workflow. Broken handoff health or missing linked artifacts remain actionable when the handoff is the active stage.

## Active Paper Flow Selection

For paper trading components, `research-status` uses the same active reviewed-flow idea as `paper-workflow-status`.

When the latest daily paper artifact used reviewed decisions, the dashboard follows `reviewed_decisions_path` to the matching paper review artifact and then uses that review's linked template-health metadata. This prevents an older unrelated warning template from making the active paper workflow look stale.

The dashboard also follows the reconciliation `report_path` recorded by the active daily paper metadata. A failed reconciliation artifact that was created as a separate synthetic/manual diagnostic remains discoverable, but it is not treated as the active paper workflow blocker unless it is linked to the active daily run. Active linked reconciliation failures still produce actionable failure status.

When reconciliation metadata declares `artifact_scope=diagnostic`, `research-status` treats the failure as diagnostic context through the paper workflow status layer. Diagnostic failures remain visible, while active scoped reconciliation failures remain actionable blockers.

Stale artifacts are still useful audit evidence. They remain available in paper indexes and health reports, and stale warning counts may be noted, but the unified dashboard stage follows the active daily reviewed workflow chain.

If a paper workflow has already advanced beyond the market-update-handoff stage, the paper workflow state takes precedence. Older handoff warnings or failures remain visible as stale audit context and do not move the active stage back to "run current-to-paper."

The same priority principle applies to historical backfill and reviewed cache exports: earlier WARN/FAIL context remains visible, but it does not regress a more advanced valid paper workflow stage.

When `paper-workflow-status` reports a reviewed WATCH_ONLY/no-fills demo state, `research-status` inherits the expected demo warning classification and keeps the next action on the demo paper workflow path. This means no-fills warnings stay visible, but they are not presented as generic broken-artifact warnings when there are zero approvals, zero open positions, zero closed trades, and no broker/live-trading markers.

## Warning Actionability

`research-status` preserves raw warning counts and adds actionability counts inherited from component dashboards where available:

- `EXPECTED_DEMO_WARNING`: expected in explicit local dry-run workflows, such as a `WATCH_ONLY` paper daily run with no fills.
- `EXPECTED_REVIEWABLE_WARNING`: expected but reviewable local dry-run warnings, such as historical backfill WARN tasks from provisional ETF/Sina policy or a known first-window `pre_close` caveat.
- `STALE_ARTIFACT_WARNING`: warning from an older dry-run artifact that is no longer part of the active workflow chain.
- `ACTIVE_SNAPSHOT_WARNING`: warning from the snapshot linked to the active workflow chain.
- `ACTIVE_SNAPSHOT_ERROR`: error from the snapshot linked to the active workflow chain.
- `STALE_SNAPSHOT_WARNING` / `UNRELATED_SNAPSHOT_WARNING`: standalone snapshot-quality warning that remains visible but is not part of the active linked chain.
- `LINKED_SNAPSHOT_PASS`: the active linked workflow snapshot passed.
- `MISSING_LINKED_SNAPSHOT`: the active workflow exists but did not expose enough snapshot linkage metadata.
- `ACTIONABLE_WARNING`: warning that should be reviewed before continuing.
- `BLOCKING_ERROR`: missing, unreadable, or failed active artifacts.

If the only warnings are expected reviewable, expected demo, or stale artifact warnings, the dashboard does not treat them as active blockers. It keeps the raw `WARN` status for audit visibility and recommends the specific next action instead of the generic `Review warnings/errors` prompt.

Prior current-candidate health warnings from old dry runs can be classified as stale when the health issue `run_id` does not match the active current-candidate run.

## Stage Meanings

- `NO_DATA`: no useful local workflow artifacts were found.
- `BACKFILL_WARNINGS_NEED_REVIEW`: historical backfill dry-run completed with reviewable warnings; review before any cache write.
- `BACKFILL_PARTIAL_WITH_REJECTIONS`: explicit historical backfill wrote accepted rows while protective preflight rejected other rows; review rejected rows before expanding or rerunning.
- `BACKFILL_CACHE_WRITE_READY`: historical backfill passed and could be considered for explicit cache write after manual review.
- `BACKFILL_COMPLETED`: historical backfill cache write occurred; run cache status and downstream data quality before research use.
- `BACKFILL_FAILED`: historical backfill has active failure and needs repair or rerun.
- `POLICY_PLAN_READY_FOR_REVIEW`: policy recommendations exist and should be reviewed before export.
- `POLICY_PLAN_WARNINGS_NEED_REVIEW`: policy recommendations have reviewable warnings, such as provisional ETF/Sina fields.
- `POLICY_PLAN_COMPARISON_WARNINGS_NEED_REVIEW`: policy recommendations include source-comparison failures or warnings that should be reviewed before export.
- `POLICY_PLAN_FAILED`: policy recommendation artifacts have active failures and need repair.
- `REVIEWED_MANIFEST_READY`: generated reviewed cache export manifest exists and can be inspected before explicit export.
- `EXPORT_READY_FROM_POLICY_PLAN`: linked export from the generated manifest exists.
- `SNAPSHOT_READY_FROM_POLICY_PLAN`: linked export/snapshot validation from the policy plan has passed; current-candidates is next unless later workflow artifacts already exist.
- `CACHE_EXPORT_READY`: reviewed cache export exists and is ready for downstream validation.
- `PIPELINE_READY_FROM_EXPORT`: data-pipeline has run from the reviewed cache export.
- `DATA_QUALITY_READY_FROM_EXPORT`: data-quality has passed for the reviewed cache export pipeline output.
- `SNAPSHOT_READY_FROM_EXPORT`: snapshot-quality passed for the reviewed cache export and current-candidates is next.
- `SIGNAL_SEMANTICS_READY_FOR_REVIEW`: semantics labels exist and should be reviewed manually; `REVIEW_BUY_CANDIDATE` is not an order.
- `DEMO_SIGNAL_SEMANTICS_VALIDATED`: demo-only semantics labels exist; this is workflow validation only, not strategy advice.
- `SIGNAL_SEMANTICS_HEALTH_WARN`: semantics artifacts have health warnings that should be reviewed before using advisory labels.
- `SIGNAL_SEMANTICS_FAILED`: semantics artifacts have active safety or artifact failures and need repair.
- `SIGNAL_ADVISORY_READY_FOR_REVIEW`: advisory signals exist and the local alert preview should be reviewed manually.
- `DEMO_SIGNAL_ADVISORY_VALIDATED`: demo-only advisory signals and alert preview exist; this is workflow validation only, not strategy advice.
- `SIGNAL_ADVISORY_HEALTH_WARN`: advisory artifacts have health warnings that should be reviewed before using alert previews.
- `SIGNAL_ADVISORY_FAILED`: advisory artifacts have active safety or artifact failures and need repair.
- `SINGLE_SYMBOL_ADVISORY_READY_FOR_REVIEW`: one-symbol advisory review exists and should be reviewed manually.
- `DEMO_SINGLE_SYMBOL_ADVISORY_VALIDATED`: demo-only one-symbol advisory exists; this is workflow validation only, not strategy advice.
- `SINGLE_SYMBOL_ADVISORY_NOT_FOUND`: requested symbol was absent from the provided local artifact and no recommendation was invented.
- `SINGLE_SYMBOL_ADVISORY_HEALTH_WARN`: one-symbol advisory artifacts have health warnings that should be reviewed before use.
- `SINGLE_SYMBOL_ADVISORY_FAILED`: one-symbol advisory artifacts have active safety or artifact failures and need repair.
- `SINGLE_SYMBOL_ADVISORY_ANSWER_READY_FOR_REVIEW`: question-style answer exists and should be reviewed manually.
- `DEMO_SINGLE_SYMBOL_ADVISORY_ANSWER_VALIDATED`: demo-only question-style answer exists; this is workflow validation only, not strategy advice.
- `SINGLE_SYMBOL_ADVISORY_ANSWER_NOT_FOUND`: requested symbol was absent from the provided local artifact and no recommendation was invented.
- `SINGLE_SYMBOL_ADVISORY_ANSWER_HEALTH_WARN`: question-style answer artifacts have health warnings that should be reviewed before use.
- `SINGLE_SYMBOL_ADVISORY_ANSWER_FAILED`: question-style answer artifacts have active safety or artifact failures and need repair.
- `ADVISORY_CONVERSATION_READY_FOR_REVIEW`: deterministic local conversation output exists and should be reviewed manually.
- `DEMO_ADVISORY_CONVERSATION_VALIDATED`: demo-only conversation output exists; this is workflow validation only, not strategy advice.
- `ADVISORY_CONVERSATION_PARSE_FAILED`: no six-digit local symbol was parsed and no recommendation was invented.
- `ADVISORY_CONVERSATION_NOT_FOUND`: parsed symbol was absent from the provided local artifact and no recommendation was invented.
- `ADVISORY_CONVERSATION_HEALTH_WARN`: conversation artifacts have health warnings that should be reviewed before use.
- `ADVISORY_CONVERSATION_FAILED`: conversation artifacts have active safety or artifact failures and need repair.
- `CACHE_EXPORT_HEALTH_WARN`: reviewed cache export has warnings that should be inspected before downstream use.
- `CACHE_EXPORT_FAILED`: reviewed cache export has active health or duplicate-key failures.
- `DATA_PREPARATION_READY`: data preparation status exists; current candidates are next.
- `SNAPSHOT_READY`: snapshot quality exists; current candidates are next.
- `CURRENT_CANDIDATES_READY`: current-candidate artifacts exist; index/health checks are next.
- `CURRENT_CANDIDATES_HEALTH_READY`: current-candidate health exists; current-to-paper is next.
- `CURRENT_CANDIDATES_READY_FOR_PAPER_SMOKE_TEST`: a market-update-handoff produced current candidates ready for a local paper workflow smoke test.
- `PAPER_HANDOFF_READY`: current-to-paper handoff exists; review template generation is next.
- `REVIEW_TEMPLATE_READY`: review template exists and needs manual editing.
- `REVIEW_TEMPLATE_HEALTH_READY`: template health passed; review decisions can be applied.
- `REVIEW_APPLIED`: reviewed decisions exist; daily paper trading is next.
- `PAPER_DAILY_READY`: daily paper report exists; manual fills and reconciliation are next.
- `RECONCILIATION_READY`: reconciliation exists; paper workflow status is next.
- `PAPER_WORKFLOW_READY`: paper workflow status exists and should be reviewed.
- `LOCAL_RESEARCH_WORKFLOW_COMPLETE`: the discovered workflow appears complete.
- `LOCAL_RESEARCH_NEEDS_ATTENTION`: at least one warning or error needs review.

## Next Manual Action Logic

The dashboard recommends one conservative next step, such as:

- Run `data-pipeline`.
- Run `current-candidates`.
- Run `current-candidates-index`.
- Run `current-candidates-health`.
- Run `current-to-paper`.
- Run `current-to-paper-review`.
- Manually edit `review_updates_template.csv`.
- Run `paper-review-decisions --health-check`.
- Run `paper-daily --reviewed-decisions`.
- Enter manual fills CSV.
- Run `paper-reconcile-fills`.
- Run `paper-workflow-status`.
- Review warnings/errors.
- Continue or clean up expected demo/stale warning artifacts when they are not active blockers.

These prompts are workflow reminders, not trading advice.

## CLI Usage

Build the unified dashboard from the default report root:

```powershell
python -m quant_replay_system.cli research-status --root outputs/reports
```

Filter by decision date and universe:

```powershell
python -m quant_replay_system.cli research-status --root outputs/reports --decision-date 2024-05-20 --universe etf_core
```

Write to a custom output directory:

```powershell
python -m quant_replay_system.cli research-status --root outputs/reports --output-dir outputs/reports/local_research_dashboard
```

Strict mode exits non-zero when the dashboard status is `WARN`:

```powershell
python -m quant_replay_system.cli research-status --root outputs/reports --strict
```

The CLI prints:

- overall status,
- workflow stage,
- latest decision date,
- next manual action,
- report path,
- `No live trading or broker API was invoked.`

## Artifact Outputs

Default output folder:

```text
outputs/reports/local_research_dashboard/<dashboard_id>/
```

Files:

- `local_research_dashboard.md`
- `local_research_dashboard.csv`
- `local_research_summary.csv`
- `metadata.json`

`dashboard_id` is deterministic from the decision date filter, discovered artifact IDs, statuses, and config version.

## Relationship To Other Dashboards

- `data-prep-status` focuses on local data preparation.
- `paper-workflow-status` focuses on the manual paper trading workflow.
- `research-status` combines those local artifact signals with current-candidate and handoff artifacts into one top-level view.

## Local-Only Guarantee

The dashboard only reads local metadata and writes local report artifacts.

It does not:

- place orders,
- connect to brokers,
- automate manual review,
- auto-approve trades,
- call network APIs,
- read or print secrets.

## Known MVP Limitations

- Uses local metadata only.
- Does not repair missing or stale artifact references.
- Does not validate full CSV schemas; artifact health modules handle file readability.
- Does not rerun failed data-prep, current-candidate, or paper workflow steps.
- Stage inference is conservative when metadata is incomplete.
