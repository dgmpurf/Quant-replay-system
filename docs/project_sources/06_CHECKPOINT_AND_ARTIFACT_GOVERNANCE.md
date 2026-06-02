# Checkpoint and Artifact Governance

> Status: working memory document  
> Last generated: 2026-06-02  
> Permanence: temporary; update after checkpoint policy or artifact-status semantics change.

## Checkpoint Philosophy

A checkpoint should happen when:

- a module is stable;
- tests pass;
- safety boundaries are preserved;
- generated artifacts are not tracked;
- the next branch would be meaningfully different.

Checkpoint docs live under:

```text
docs/release_checkpoint_vX.Y.Z.md
```

They are milestone summaries, not production readiness claims.

## Artifact Governance Pattern

Most generated artifact workflows should have:

```text
artifact command
→ index
→ health
→ status
→ research-status integration
```

This makes artifacts discoverable and prevents hidden state transitions.

## Active vs Legacy Artifacts

Keep legacy artifacts visible, but do not let them drive active workflow status.

Examples include stale snapshots, old review artifacts, diagnostic reconciliation failures, partial historical backfill rejections, old backfill plans without warmup fields, legacy advisory artifacts missing provenance, and stale PIT overlay review artifacts missing newer metadata columns.

## Diagnostic vs Active Artifacts

Diagnostic artifacts should remain visible but not block active workflow unless linked.

Examples:

- synthetic PIT universe metadata support smoke;
- synthetic export-ready diagnostics under `manual_diagnostics`;
- ignored dry-run files.

## Plan-Only Workflows

Plan-only workflows include:

- `current-candidates-backfill-plan`
- `current-candidates-backfill-execution-manifest`
- `pit-universe-overlay-plan`
- calibration-to-signal-semantics proposal reports

Plan-only means no candidate generation, no snapshot build, no forward labels, no cache mutation, no messages, and no broker/order behavior.

## Review-Template Workflows

PIT universe overlay plans are review-template workflows. `NEEDS_MANUAL_REVIEW` rows are not valid PIT universe rows until reviewed.

## Review-Only Workflows

PIT universe overlay review artifacts may create statuses:

```text
NEEDS_MANUAL_REVIEW
APPROVED_FOR_PIT_UNIVERSE
REJECTED
NEEDS_MORE_EVIDENCE
```

Review-only does not mean exported universe input. Approved review rows are not the same as accepted current-candidates universe files.

## Evidence Completion Helper Workflows

Evidence completion helper artifacts may produce:

- evidence completion templates;
- evidence gap reports;
- non-authoritative `suggested_*` hints.

They must not approve rows, set `valid_for_signal_date=true`, convert future-dated hints into evidence, export universe files, or write `data/raw` / `data/processed`.

## Evidence Review Worklist Workflows

Evidence review worklist artifacts are worklist-only.

They may produce:

- row-level worklists;
- symbol summaries;
- date summaries;
- reviewer update templates.

They must not approve rows, set `valid_for_signal_date=true`, export universe files, write `data/raw` / `data/processed`, run current-candidates, build snapshots, or compute forward labels.

A worklist is not evidence; it only organizes what a reviewer needs to fill.

## Evidence Update Ingestion Workflows

A future PIT universe evidence update ingestion workflow should validate reviewer-completed worklist updates and produce a clean `review_updates.csv` artifact.

It should block ingestion when:

- identity keys are missing;
- duplicate `signal_date + symbol + universe_name` rows exist;
- reviewer/reviewed_at is missing;
- evidence source/path/reference is missing;
- approval is requested but survivorship risk is unresolved;
- PIT dates are invalid;
- suggested fields are copied into authoritative fields without review reason.

It should not export universe files, write `data/raw`, write `data/processed`, run current-candidates, build snapshots, or compute forward labels.

## Export-Readiness Workflows

Export-readiness blocks export when there are no approved rows, evidence is missing, survivorship is unresolved, required universe columns are missing, duplicates exist, or PIT dates are invalid. It must not write `data/raw` or `data/processed`.

## Export-Staging Workflows

Export staging is guarded and outputs-only. It may create reviewable previews under:

```text
outputs/reports/point_in_time_universe_export_staging/<staging_id>/
```

Staging previews are not accepted local universe inputs.

## Safety Flags

Relevant artifact metadata should include:

```text
no_live_trading
no_broker_api
no_order_placement
no_message_sent
auto_order_allowed=false
requires_manual_confirmation=true
llm_api_called=false
plan_only=true
review_only=true
evidence_completion_only=true
worklist_only=true
export_readiness_only=true
staging_only=true
```

## Survivorship and Point-in-Time Governance

Universe, fundamental, and event data must preserve PIT validity.

Important fields:

```text
as_of_date
available_time
listed_date
delisted_date
revision_id
source
evidence_path
evidence_reference
review_status
reviewer
reviewed_at
```

Rows derived from a future universe must keep survivorship-bias warnings until reviewed. Rows cannot be exported into usable current-candidates universe input until export-readiness and export/staging gates confirm required metadata.

## Research-Status Priority Rule

`research-status` should summarize context while preserving later workflow priority.

Safe parse failures, stale warnings, planning blockers, review evidence blockers, export-readiness blockers, staging blockers, and worklist blockers should not override later validated paper workflow unless they represent an active blocking error for the current workflow.

## When to Refresh This Document

Refresh when:

- new artifact types are added;
- index/health/status patterns change;
- research-status priority changes;
- diagnostic artifact scoping changes;
- PIT evidence update ingestion semantics are implemented;
- accepted PIT universe export semantics are implemented;
- snapshot preparation semantics are implemented;
- real alert delivery or broker integration is introduced.
