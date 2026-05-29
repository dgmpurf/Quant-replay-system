# Checkpoint and Artifact Governance

> Status: working memory document  
> Last generated: 2026-05-28  
> Permanence: temporary; update after checkpoint policy changes.

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

They are not final product documentation. They are milestone summaries.

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

## Plan-Only Workflows

The project has several plan-only workflows. These must not be confused with execution:

- `current-candidates-backfill-plan`
- `current-candidates-backfill-execution-manifest`
- future PIT universe overlay plans
- calibration-to-signal-semantics proposal reports

Plan-only means:

- no candidate generation,
- no snapshot build,
- no forward labels,
- no cache mutation,
- no message sending,
- no broker/order behavior.

## Research-Status Priority Rule

`research-status` should summarize context from many layers while preserving later workflow priority.

A safe parse failure, NOT_FOUND, stale warning, or planning blocker should not override a later validated paper workflow unless it represents an active blocking error for the current workflow.

## When to Refresh This Document

Refresh this document when:

- new artifact types are added,
- new index/health/status patterns appear,
- legacy/stale actionability rules change,
- research-status stage priority changes,
- diagnostic artifact scoping changes,
- real alert delivery or broker integration is introduced.
