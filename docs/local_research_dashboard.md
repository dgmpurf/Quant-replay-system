# Unified Local Research Workflow Dashboard v0.1

The Unified Local Research Workflow Dashboard is a local-only top-level status report for the research flow from data preparation to current candidates to manual paper trading.

It does not connect to brokers, place orders, automate execution, auto-approve trades, print secrets, or call network APIs.

## Purpose

The project now has separate dashboards and health checks for data preparation, current-candidate artifacts, and paper trading. The unified dashboard answers:

- Has data preparation produced usable artifacts?
- Has snapshot quality run?
- Has a historical backfill dry-run or cache-write run produced reviewable artifact evidence?
- Has a policy-aware reviewed cache export plan produced a reviewable manifest or linked downstream validation?
- Has a reviewed offline market update handoff produced snapshot/current-candidate artifacts?
- Have current candidates been generated?
- Are current-candidate artifacts healthy?
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
