# Historical Replay Mixed STOCK/ETF Universe Profile Policy Next-Task Wording Hardening v0.1

## Purpose

This report records a wording-only hardening for the live recommended next task after the generated artifact review of the Historical Replay Mixed STOCK/ETF Universe Profile Policy fixture.

The live next task was updated from the generated artifact review route to:

`Historical Replay Mixed STOCK/ETF Universe Profile Policy Checkpoint Documentation Bundle Report-Only v0.1`

## Scope

This change updates only live next-task wording surfaces for the mixed STOCK/ETF universe profile policy fixture:

- core metadata and markdown report output
- CLI stdout
- index/status outputs through the shared core next-task constant
- research-status/dashboard summary context
- focused test expectations

## Preserved Semantics

The hardening does not change schema, row set, counts, status vocabulary, blocker vocabulary, health behavior, evidence behavior, PIT behavior, replay behavior, buy-review behavior, or trading behavior.

The selected sample remains:

- historical_decision_date: `2024-04-02`
- universe: `etf_core`
- row_count: `9`
- stock_row_count: `7`
- etf_row_count: `2`
- profile_conflict_count: `7`
- profile_policy_accepted_count: `0`
- universe_membership_approved_count: `0`
- official_status_evidence_accepted_count: `0`
- safety_true_count: `0`

## Safety Boundary

This wording hardening does not collect official evidence, fill evidence templates, accept no-hit context, accept official evidence, close evidence, approve PIT, resolve profile conflicts, approve universe membership, validate stock_profile, create replay input, run replay, freeze decisions, create labels, compute metrics, train models, expand paper workflow, allow buy-review, allow trading, call broker/API/order/message/LLM surfaces, write protected data, create docs/project_sources, create Project Source packages, or update Source notes.

## Validation Summary

- RED-equivalent observation confirmed the old generated artifact review route existed in live source/test expectations before the fix.
- Focused mixed profile fixture/views/CLI tests passed after the fix.
- Dashboard/research-status focused tests passed after the fix.
- Combined focused suite passed after the fix.
- Temp-root CLI smoke passed for core, index, health, status, and research-status.
- Temp-root artifacts stayed outside the repository and retained the expected 8 mixed profile files.

## Decision

Classification:
`HISTORICAL_REPLAY_MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_NEXT_TASK_WORDING_HARDENED_REPORT_ONLY`

Verdict:
`HISTORICAL_REPLAY_MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_READY_FOR_CHECKPOINT_DOCUMENTATION_BUNDLE_REPORT_ONLY`

Recommended next task:
`Historical Replay Mixed STOCK/ETF Universe Profile Policy Checkpoint Documentation Bundle Report-Only v0.1`

Recommended tag:
No tag for this wording hardening.

Recommended Source update:
No Source update for this wording hardening.
