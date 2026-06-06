# Release Checkpoint v1.25.0

## Scope

v1.25.0 adds artifact views and unified `research-status` integration for the report-only one-row material evidence fill package workflow.

The active one-row package is:

- `package_id`: `136cbd739ca1`
- target row: `2024-04-02 / 000001 / stock_core`
- package row count: `1`
- context fields drafted: `17`
- material blockers closed: `0`
- checklist-pass candidates: `0`
- remaining blocked rows: `16`

## Commands

```bash
python -m quant_replay_system.cli one-row-material-evidence-fill-package-index
python -m quant_replay_system.cli one-row-material-evidence-fill-package-health
python -m quant_replay_system.cli one-row-material-evidence-fill-package-status
python -m quant_replay_system.cli research-status
```

## Research-Status Integration

`research-status` now exposes the latest one-row material evidence fill package as PIT evidence-preparation context:

- latest package id
- status, stage, and health status
- target signal date, symbol, and universe name
- package row count
- context-field-drafted count
- material-blocker-closed count
- checklist-pass candidate count
- remaining-blocked count
- clean-review-updates-created flag
- approval-applied flag
- report path
- next manual action

Later paper workflow priority is preserved. One-row package warnings are expected reviewable context, not candidate generation failure, export failure, paper workflow failure, or strategy-performance validation.

## Safety

The workflow remains report-only:

- no PIT approval
- no `APPROVED_FOR_PIT_UNIVERSE`
- no `include_flag=true`
- no `valid_for_signal_date=true`
- no `survivorship_bias_resolved=true`
- no clean `review_updates.csv`
- no PIT review
- no export-readiness
- no staging
- no universe export
- no `data/raw` write
- no `data/processed` write
- no current-candidates generation
- no snapshot build
- no forward labels
- no live trading
- no broker integration
- no orders
- no messages
- no cache mutation

## Status

The current package drafts context fields only. It does not close material PIT blockers and does not create checklist-pass candidates. Reviewer evidence, no-hit acceptance, survivorship rationale, and approval-grade PIT evidence remain required before any clean review update can be produced in a later explicit workflow.
