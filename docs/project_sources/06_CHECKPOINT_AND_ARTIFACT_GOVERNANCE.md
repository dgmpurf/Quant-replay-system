# Checkpoint and Artifact Governance

> Status: working memory document  
> Last generated: 2026-05-29  
> Permanence: temporary; update after checkpoint policy or artifact-status semantics change.

## Checkpoint Philosophy

This project uses checkpoint docs and Git tags to control complexity.

A checkpoint should happen when:

- a module is stable,
- tests pass,
- safety boundaries are preserved,
- generated artifacts are not tracked,
- the next branch would be meaningfully different.

Checkpoint documents live under:

```text
docs/release_checkpoint_vX.Y.Z.md
```

They are milestone summaries, not final product documentation.

## Checkpoint Does Not Mean Production Ready

Checkpoint docs mean:

```text
this local capability is implemented and tested under current assumptions
```

They do not mean:

```text
strategy validated
live trading ready
broker integration approved
profitability proven
```

## Artifact Governance Pattern

Most generated artifact workflows should have:

```text
artifact command
→ index
→ health
→ status
→ research-status integration
```

This makes artifacts discoverable and prevents hidden state.

## Active vs Legacy Artifacts

The project repeatedly encountered stale/legacy artifacts. The preferred pattern is:

```text
keep legacy artifacts visible
but do not let them drive active workflow status
```

Examples already established:

- stale snapshot warnings,
- old paper review artifacts,
- diagnostic reconciliation failures,
- partial historical backfill rejections,
- old current-candidates backfill plans without warmup fields,
- legacy advisory artifacts missing semantics provenance.

## Diagnostic vs Active Artifacts

Diagnostic artifacts should remain visible but should not block the active workflow unless linked.

Examples:

- synthetic WATCH_ONLY fill failure,
- manual diagnostics reconciliation artifacts,
- ignored dry-run files.

If possible, diagnostic artifacts should include explicit metadata such as:

```text
artifact_scope=diagnostic
diagnostic_artifact=true
active_workflow_artifact=false
```

## Plan-Only Workflows

The project has several plan-only workflows. These must not be confused with execution:

- `current-candidates-backfill-plan`
- `current-candidates-backfill-execution-manifest`
- `pit-universe-overlay-plan`
- calibration-to-signal-semantics proposal reports
- future snapshot preparation plans
- future export-readiness plans

Plan-only means:

- no candidate generation,
- no snapshot build,
- no forward labels,
- no cache mutation,
- no message sending,
- no broker/order behavior.

## Review-Template Workflows

PIT universe overlay plans are review-template workflows.

They may create rows such as:

```text
NEEDS_MANUAL_REVIEW
```

But those rows are not valid PIT universe rows until a separate approval workflow verifies evidence and writes reviewed artifacts.

A review-template artifact should not be used by current-candidates, snapshot manifests, or forward-label workflows as if it were approved data.

## Review-Only Workflows

PIT universe overlay review artifacts are review-only workflows.

They may create statuses such as:

```text
NEEDS_MANUAL_REVIEW
APPROVED_FOR_PIT_UNIVERSE
REJECTED
NEEDS_MORE_EVIDENCE
```

Review-only means:

- reviewed evidence may be recorded;
- rows may become approved for PIT universe semantics;
- no usable universe files are exported unless a separate guarded export workflow does that;
- no current-candidates are generated;
- no snapshots are built;
- no forward labels are computed.

Approved review rows are not the same thing as exported current-candidates universe input.

## Export-Readiness Workflows

A future PIT universe export readiness workflow should answer whether approved review rows can be exported.

It should block export when:

- there are no approved rows,
- approved rows are not `valid_for_signal_date=true`,
- survivorship-bias warnings are unresolved,
- required evidence is missing,
- required current-candidates universe columns are missing,
- duplicate `signal_date + symbol + universe_name` rows exist.

Export readiness should still not write `data/raw` or `data/processed` unless a separate explicit export workflow and accept flag are introduced.

## Safety Flags

Artifact metadata should include safety flags where relevant:

- `no_live_trading`
- `no_broker_api`
- `no_order_placement`
- `no_message_sent`
- `auto_order_allowed=false`
- `requires_manual_confirmation=true`
- `llm_api_called=false`
- `plan_only=true`
- `review_only=true`

## Survivorship and Point-in-Time Governance

Universe, fundamental, and event data must preserve point-in-time validity.

Important fields include:

- `as_of_date`
- `available_time`
- `listed_date`
- `delisted_date`
- `revision_id`
- `source`
- `evidence_path`
- `evidence_reference`
- `review_status`
- `reviewer`
- `reviewed_at`

Rows derived from a future universe must carry survivorship-bias warnings until separately reviewed.

Rows cannot be approved for PIT universe use unless evidence is present and survivorship risk is resolved.

## Research-Status Priority Rule

`research-status` should summarize context from many layers while preserving later workflow priority.

A safe parse failure, NOT_FOUND, stale warning, planning blocker, or review evidence blocker should not override a later validated paper workflow unless it represents an active blocking error for the current workflow.

Examples:

- PIT overlay rows needing review should be visible.
- PIT review rows needing evidence should be visible.
- They should not be treated as candidate generation failures.
- They should not override later validated paper workflow status.

## When to Refresh This Document

Refresh this document when:

- new artifact types are added,
- new index/health/status patterns appear,
- legacy/stale actionability rules change,
- research-status stage priority changes,
- diagnostic artifact scoping changes,
- PIT universe export readiness or export semantics are implemented,
- real alert delivery or broker integration is introduced.
