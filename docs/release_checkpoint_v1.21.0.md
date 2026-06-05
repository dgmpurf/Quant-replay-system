# Release Checkpoint v1.21.0

First-Batch Reviewer Evidence Completion Planning.

Recommended tag: `v1.21.0`

## Completed Capabilities

- Added `first-batch-reviewer-evidence-completion-plan` as a report-only planning workflow.
- Added index, health, and status views for first-batch reviewer evidence completion plan artifacts.
- Integrated first-batch completion plan status into unified `research-status`.
- Exposed reviewer completion, no-hit acceptance, survivorship rationale, metadata completion, checklist pass, remaining blocked, clean-review-update, and approval-applied fields.
- Preserved later paper workflow priority while keeping first-batch completion context visible.

## Workflow Impact

The workflow converts existing first-batch context into manual evidence completion tasks only. It reads activated replacement evidence update planning, reviewer no-hit downstream impact, official status packet enrichment, checklist validator, and policy comparison context.

Expected active state after this checkpoint:

- first-batch rows: `16`
- stock_core rows: `8`
- etf_core rows: `8`
- reviewer completion required: `16`
- no-hit acceptance required: `16`
- survivorship rationale required: `16`
- checklist pass count: `0`
- remaining blocked count: `16`
- clean review updates created: `false`
- approval applied: `false`

## Safety Guarantees

- No PIT approvals are applied.
- No rows are rejected.
- No `APPROVED_FOR_PIT_UNIVERSE` rows are created.
- No `include_flag=true` or `valid_for_signal_date=true` rows are created.
- No clean `review_updates.csv` is created.
- No PIT review is run.
- No export-readiness or staging workflow is run.
- No universe export occurs.
- No `data/raw` or `data/processed` write occurs.
- No active worklist or cache mutation occurs.
- No current-candidates generation occurs.
- No snapshot build or forward labels occur.
- No live trading, broker API, automated orders, or message delivery is implemented.
- No strategy performance validation is claimed.

## Known Limitations

- The workflow does not complete evidence automatically.
- Reviewer no-hit context remains supporting context only.
- Official quotation evidence remains date-specific traded context only.
- Not-delisted, ST/no-ST, survivorship rationale, and metadata completion still require human-reviewed evidence.
- Active first-batch rows remain blocked until a later evidence update validation workflow succeeds.

## Recommended Next Engineering Tasks

1. Prepare a diagnostics-only manual completion pack from the new `reviewer_completion_template.csv`.
2. Complete reviewer no-hit acceptance and survivorship rationale fields manually where source coverage is sufficient.
3. Rerun diagnostics-only ingestion/checklist/policy comparison after manual evidence completion.
4. Keep PIT approval, export readiness, staging, and current-candidates generation separate until evidence passes validation.
