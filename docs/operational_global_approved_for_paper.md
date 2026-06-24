# Operational Global APPROVED_FOR_PAPER Planning

`operational-global-approved-for-paper` is a report-only planning workflow for
reviewing whether prior Global APPROVED_FOR_PAPER Approval Review artifacts are ready
for a later, separate operational approval decision.

The current planning status is:

`OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED`

This status means planning artifacts were created as governance context only. It does
not grant operational global APPROVED_FOR_PAPER, is not real buy-review eligibility,
does not set buy_review_allowed, and is not strategy performance validation.

## Commands

- `operational-global-approved-for-paper`
- `operational-global-approved-for-paper-index`
- `operational-global-approved-for-paper-health`
- `operational-global-approved-for-paper-status`

## Research-Status Fields

`research-status` exposes the latest operational planning run id, status, health,
workflow stage, artifact path, approval scope, approval expiry, revocation path, report
path, next action, and downstream safety flags. These fields are scoped to report-only
planning context.

Important distinctions:

- report-only Operational Global APPROVED_FOR_PAPER planning does not grant operational global APPROVED_FOR_PAPER.
- report-only Operational Global APPROVED_FOR_PAPER planning is not real buy-review eligibility.
- report-only Operational Global APPROVED_FOR_PAPER planning does not set buy_review_allowed.
- report-only Operational Global APPROVED_FOR_PAPER planning is not strategy performance validation.
- report-only Operational Global APPROVED_FOR_PAPER planning does not authorize current-candidates.
- report-only Operational Global APPROVED_FOR_PAPER planning does not authorize snapshots.
- report-only Operational Global APPROVED_FOR_PAPER planning does not authorize signal_semantics mutation.
- report-only Operational Global APPROVED_FOR_PAPER planning does not authorize active stock_profile.
- report-only Operational Global APPROVED_FOR_PAPER planning does not authorize promoted/production models.
- report-only Operational Global APPROVED_FOR_PAPER planning does not authorize active thresholds.
- report-only Operational Global APPROVED_FOR_PAPER planning does not authorize advisory predictions/probabilities.
- report-only Operational Global APPROVED_FOR_PAPER planning does not authorize broker/order/message/API/trading.

## Fail-Closed Behavior

If artifacts are absent, health is missing, or health is not PASS, operational planning
remains bounded to report-only context. It must not fabricate operational global
APPROVED_FOR_PAPER, real buy-review eligibility, buy_review_allowed, strategy
performance validation, current-candidates integration, snapshot integration, signal
semantics mutation, model promotion, stock-profile activation, API behavior, or trading.

## Future Work

Any future real buy-review / performance / trading workflow requires separate exact
approval. This workflow only prepares planning evidence and status visibility for later
human review.
