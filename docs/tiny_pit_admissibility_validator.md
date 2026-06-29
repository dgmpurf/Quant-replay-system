# Tiny PIT Admissibility Validator

The Tiny PIT Admissibility Validator is a synthetic, report-only prototype for validating the future PIT admissibility contract over reviewed LOCAL_CSV replay prototype inputs.

It is not a real PIT validator. It does not create real reviewed CSV packages, active reviewed input candidates, real replay inputs, active replay input, replay evidence bundles, replay decisions, replay decision freezes, forward labels, future-label joins, training datasets, metric computation, signal_score implementation, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review eligibility, strategy performance validation, current-candidates, snapshots, signal_semantics mutation, broker/API/order/message behavior, or trading. No trading is authorized.

## Purpose

The synthetic validator exercises deterministic package cases derived from the v1.68.0 contract fixture and the accepted real-validator design spec. It proves report-only status, health, index, and research-status integration paths without accepting real data packages.

Current expected artifact semantics:

- Workflow stage: `TINY_PIT_ADMISSIBILITY_VALIDATOR_SYNTHETIC_CORE_CREATED`
- Runtime status: `PASS`
- Health status: `PASS`
- Case count: `14`
- Pass-candidate count: `1`
- Warning count: `3`
- Blocker count: `11`
- Report-only: `true`
- Diagnostic-only: `true`
- Synthetic-only: `true`

## Commands

Use these report-only commands:

- `tiny-pit-admissibility-validator`
- `tiny-pit-admissibility-validator-index`
- `tiny-pit-admissibility-validator-health`
- `tiny-pit-admissibility-validator-status`
- `research-status`

The status command summarizes the latest synthetic validator artifact and recommends:

`Tiny PIT Admissibility Validator Post-Checkpoint Governance Audit Report-Only v0.1`

## Artifact Root

Default artifacts are written under:

`outputs/reports/manual_diagnostics/tiny_pit_admissibility_validator_v0_1/`

Expected files per run:

- `metadata.json`
- `tiny_pit_admissibility_validator_report.md`
- `package_gate_matrix.csv`
- `timing_admissibility_matrix.csv`
- `source_lineage_matrix.csv`
- `reviewer_authority_matrix.csv`
- `quality_gate_matrix.csv`
- `output_status_contract.csv`
- `forbidden_interpretation_matrix.csv`
- `safety_flags.json`

Views are written under sibling `index/`, `health/`, and `status/` directories.

## Status Meanings

Synthetic package statuses are context only:

- `NO_INPUT`
- `PACKAGE_SCHEMA_INVALID`
- `PACKAGE_BLOCKED_MISSING_REQUIRED_SECTION`
- `PACKAGE_BLOCKED_PIT_TIMING`
- `PACKAGE_BLOCKED_SOURCE_LINEAGE`
- `PACKAGE_BLOCKED_REVIEWER_AUTHORITY`
- `PACKAGE_BLOCKED_QUALITY`
- `PACKAGE_WARN_REVIEW_REQUIRED`
- `PACKAGE_PASS_CANDIDATE_FOR_HUMAN_REVIEW`
- `PACKAGE_DIAGNOSTIC_ONLY_PASS`

No status may be interpreted as `ACTIVE_REPLAY_INPUT_READY`, active replay input, replay execution approval, label creation approval, training approval, stock_profile approval, paper approval, buy-review approval, performance validation, or trading permission.

## Research-Status Context

`research-status` exposes latest Tiny PIT synthetic validator context:

- validator id, status, health status, workflow stage, artifact path, and report path;
- case, pass-candidate, warning, and blocker counts;
- report-only, diagnostic-only, and synthetic-only flags;
- active replay input, active replay ready, and trading flags fixed false;
- reviewed CSV package, active reviewed input candidate, replay input, replay execution, forward labels, training, metric computation, signal_score, model training, stock_profile, paper validation, buy-review, performance validation, broker/API, and data-write flags fixed false.

The context is lower priority than existing paper workflow state. `PAPER_WORKFLOW_READY` must remain the final research-status workflow stage when later paper workflow context exists.

## Safety Boundary

The synthetic validator is local/report-only diagnostics. It must not:

- read or write `data/raw`, `data/processed`, or `data/cache`;
- create real reviewed CSV packages;
- create active reviewed input candidates;
- create real replay input or active replay input;
- run replay;
- create replay decisions, freezes, forward labels, label joins, training datasets, metrics, signal_score, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review eligibility, current-candidates, snapshots, signal_semantics mutations, broker/order/message/API/trading behavior, or performance validation.

## Known Limitations

This workflow validates synthetic cases only. It does not prove real PIT admissibility logic, real available_time adjudication, source reliability, reviewer authority policy, or real replay readiness.

## Recommended Next Task

Tiny PIT Admissibility Validator Post-Checkpoint Governance Audit Report-Only v0.1.
