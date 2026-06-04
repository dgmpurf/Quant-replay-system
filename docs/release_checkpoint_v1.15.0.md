# Release Checkpoint v1.15.0

## Milestone

EOD Post-Close Low-Budget PIT Policy Profile Comparison and Research Status Integration.

## Completed Capabilities

- Added `pit-evidence-policy-profile-comparison` as a report-only comparison between `STRICT_PIT` and opt-in `EOD_POST_CLOSE_LOW_BUDGET_PIT`.
- Added comparison artifacts: row comparison CSV, summary CSV, relaxed blocker matrix, remaining blocker matrix, EOD policy snapshot, report, and metadata.
- Added `pit-evidence-policy-profile-comparison-index`, `pit-evidence-policy-profile-comparison-health`, and `pit-evidence-policy-profile-comparison-status`.
- Integrated policy-profile comparison status into unified `research-status`.
- Preserved strict validator default behavior and `STRICT_PIT` as the reference profile.
- Preserved later paper workflow priority while keeping comparison fields visible as evidence-policy context.

## Workflow Impact

The workflow helps reviewers see whether an explicit EOD/post-close low-budget policy would relax only timing and same-day local-cache support blockers. It does not apply approvals or generate approval updates.

Latest local dry-run:

- `comparison_id`: `0ef6d2f3bae6`
- `status`: `WARN`
- `stage`: `PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_ALL_BLOCKED`
- `profile_name`: `EOD_POST_CLOSE_LOW_BUDGET_PIT`
- `row_count`: 16
- `strict_checklist_pass_count`: 0
- `eod_low_budget_checklist_pass_count`: 0
- `relaxed_blocker_count`: 16
- `remaining_blocked_count`: 16
- health: `PASS`
- `research-status` final `workflow_stage`: `PAPER_WORKFLOW_READY`

## Validation Baseline

Validation for this checkpoint:

- `python -m pytest`: 1503 passed, 2 warnings.
- `python -m pytest -m "not slow"`: 1394 passed, 109 deselected, 2 warnings.

## Safety Guarantees

- `EOD_POST_CLOSE_LOW_BUDGET_PIT` is opt-in only.
- `STRICT_PIT` remains the default/reference profile.
- No approval was applied.
- No `APPROVED_FOR_PIT_UNIVERSE` rows were set.
- No PIT overlay review was run.
- No export-readiness or staging workflow was run by the comparison.
- No universe export occurred.
- No active worklists were mutated.
- No `data/raw` or `data/processed` writes occurred.
- No current-candidates were generated.
- No snapshots were built.
- No forward labels were computed.
- No live trading, broker API, orders, or messages were used.
- No LLM/API/network calls are required by the workflow.
- No strategy performance validation is claimed.

## Known Limitations

- The comparison does not verify external evidence documents.
- Same-day local market cache remains supporting context only and requires `available_time <= decision_time`.
- Not-delisted, ST/no-ST, survivorship, reviewer, reviewed-at, review-reason, evidence-source, and evidence-reference gates remain strict.
- Current rows remain blocked under both strict and EOD low-budget profiles.
- The comparison does not create clean review updates or usable universe inputs.

## Recommended Next Engineering Tasks

- Continue manual evidence collection for the remaining non-relaxed PIT blockers.
- Consider a narrowly scoped source-acceptance review for same-day local cache support under EOD/post-close research policy.
- Keep profile comparison separate from strict validator defaults unless a future explicit governance step approves otherwise.

## Recommended Tag

`v1.15.0`
