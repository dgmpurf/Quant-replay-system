# Global APPROVED_FOR_PAPER Approval Review

`global-approved-for-paper-approval-review` is a report-only governance workflow for
reviewing whether prior scoped APPROVED_FOR_PAPER Phase 1 artifacts are ready for a
future, separate global approval decision.

The current approved status is:

`GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED`

This status means the review package is internally consistent as report-only governance
context. It is not real buy-review eligibility, does not set buy_review_allowed, and is
not strategy performance validation.

## Commands

- `global-approved-for-paper-approval-review`
- `global-approved-for-paper-approval-review-index`
- `global-approved-for-paper-approval-review-health`
- `global-approved-for-paper-approval-review-status`

## Research-Status Fields

`research-status` exposes the latest global approval-review run id, status, health,
workflow stage, artifact path, source lineage, and safety flags. These fields are scoped
to the report-only review.

Important distinctions:

- report-only Global APPROVED_FOR_PAPER Approval Review is not operational global APPROVED_FOR_PAPER.
- report-only Global APPROVED_FOR_PAPER Approval Review is not real buy-review eligibility.
- report-only Global APPROVED_FOR_PAPER Approval Review does not set buy_review_allowed.
- report-only Global APPROVED_FOR_PAPER Approval Review is not strategy performance validation.
- report-only Global APPROVED_FOR_PAPER Approval Review does not authorize current-candidates.
- report-only Global APPROVED_FOR_PAPER Approval Review does not authorize snapshots.
- report-only Global APPROVED_FOR_PAPER Approval Review does not authorize signal_semantics mutation.
- report-only Global APPROVED_FOR_PAPER Approval Review does not authorize active stock_profile.
- report-only Global APPROVED_FOR_PAPER Approval Review does not authorize promoted/production models.
- report-only Global APPROVED_FOR_PAPER Approval Review does not authorize active thresholds.
- report-only Global APPROVED_FOR_PAPER Approval Review does not authorize advisory predictions/probabilities.
- report-only Global APPROVED_FOR_PAPER Approval Review does not authorize broker/order/message/API/trading.

## Fail-Closed Behavior

If artifacts are absent, health is missing, or health is not PASS, the review remains
bounded to report-only context. It must not fabricate approval readiness, buy-review
permission, paper approval, performance validation, current-candidates integration,
snapshot integration, signal semantics mutation, model promotion, stock-profile
activation, API behavior, or trading.

## Future Work

Any future real buy-review / performance / trading workflow requires separate exact
approval. This workflow only prepares review evidence and status visibility for later
human review.
