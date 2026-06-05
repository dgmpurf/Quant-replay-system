# Checkpoint and Artifact Governance

> Status: working memory document  
> Last generated: 2026-06-05  
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

Do not refresh Project Source after every small audit. Refresh after accepted milestone/checkpoint/tag or when current stage, next branch, or artifact governance changes.

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

Examples include stale snapshots, old review artifacts, diagnostic reconciliation failures, partial historical backfill rejections, old backfill plans without warmup fields, legacy advisory artifacts missing provenance, stale PIT overlay review artifacts missing newer metadata columns, legacy mixed-demo `etf_core` artifacts, replacement worklist plans that are not accepted active worklists, accepted replacement planning artifacts that are not activated worklists, activated replacement planning artifacts that are not PIT-approved universe inputs, activated evidence update plans that are not clean review updates, checklist validator outputs that are not PIT approvals, policy profile comparison outputs that do not change strict validator defaults, official status evidence packets and enrichment artifacts that are not PIT approvals, reviewer no-hit source coverage acceptance artifacts that are supporting-context only, reviewer no-hit downstream impact artifacts that do not apply approvals, first-batch reviewer evidence completion plan artifacts that are planning context only, and no-hit support context that is not approval-grade evidence without reviewer acceptance.

## Diagnostic vs Active Artifacts

Diagnostic artifacts should remain visible but not block active workflow unless linked.

Examples:

- synthetic PIT universe metadata support smoke;
- synthetic export-ready diagnostics under `manual_diagnostics`;
- synthetic evidence update apply smoke;
- Codex evidence discovery diagnostics;
- policy profile audit diagnostics;
- official status source access smoke diagnostics;
- SZSE 1815 quotation probe diagnostics;
- SZSE/CNInfo exception no-hit diagnostics;
- official no-hit evidence policy diagnostics;
- PIT official status evidence packet enrichment dry-runs;
- reviewer no-hit source coverage acceptance dry-runs;
- reviewer no-hit downstream impact dry-runs;
- first-batch reviewer evidence completion plan dry-runs;
- ignored dry-run files.

## Review-Only and Evidence Workflows

PIT universe overlay review artifacts may create statuses such as `NEEDS_MANUAL_REVIEW`, `APPROVED_FOR_PIT_UNIVERSE`, `REJECTED`, and `NEEDS_MORE_EVIDENCE`, but review-only does not mean exported universe input.

Evidence completion helper artifacts, evidence review worklist artifacts, evidence update ingestion artifacts, reviewer no-hit acceptance artifacts, downstream impact artifacts, and first-batch completion planning artifacts organize, validate, or plan evidence. They must not export universe files, write `data/raw` / `data/processed`, run current-candidates, build snapshots, or compute forward labels.

A clean `review_updates.csv` is not an applied approval; it is a validated input that may be manually passed to the review workflow later.

## PIT Evidence Checklist Validator Workflows

PIT evidence checklist validator artifacts are evidence-gate reports.

They may evaluate draft or completed update CSV rows against strict stock/ETF evidence checklists, produce missing-evidence matrices, produce approval-candidate previews, and expose checklist pass/block counts in research-status.

They must not apply approvals, set `APPROVED_FOR_PIT_UNIVERSE`, run PIT review, run export-readiness, run staging, export universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, or compute forward labels.

A checklist-pass row is only an approval-candidate preview. It still requires explicit PIT review before any approval artifact exists.

## PIT Evidence Policy Profile Comparison Workflows

PIT evidence policy profile comparison artifacts are report-only policy context.

They may compare `STRICT_PIT` with opt-in profiles such as `EOD_POST_CLOSE_LOW_BUDGET_PIT` and `EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT`, report relaxed blockers, no-hit context support, reviewer-acceptance requirements, and remaining blockers.

They must not change strict validator default behavior, apply approvals, set `APPROVED_FOR_PIT_UNIVERSE`, create approval update CSVs, run PIT review/export-readiness/staging, export universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, or compute forward labels.

Known profiles:

```text
STRICT_PIT
EOD_POST_CLOSE_LOW_BUDGET_PIT
EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT
```

## PIT Official Status Evidence Packet and Enrichment Workflows

PIT official status evidence packet artifacts and enrichment artifacts are evidence-packet reports.

They may combine source access smoke results, prior evidence discovery diagnostics, local EOD cache context, official symbol-level sources, SZSE 1815 same-date quotation diagnostics, reviewed no-hit support context, and enrichment lineage into per-symbol/per-date packets.

They may classify evidence as:

```text
STRONG_OFFICIAL_DATE_SPECIFIC
STRONG_OFFICIAL_DATE_SPECIFIC_QUOTATION
SUPPORTING_OFFICIAL_SYMBOL_LEVEL
SUPPORTING_LOCAL_EOD_CACHE
REVIEWED_NO_HIT_SUPPORT_CONTEXT
CONTEXT_ONLY
MISSING
```

They must not apply approvals, set `APPROVED_FOR_PIT_UNIVERSE` as an applied value, treat supporting official symbol-level evidence as date-specific proof, treat local EOD cache as official date-specific proof, treat no-hit observations as approval-grade without explicit reviewer acceptance and documented source coverage, run PIT review/export-readiness/staging, export universe files, write `data/raw` or `data/processed`, mutate active worklists, mutate market cache, run current-candidates, build snapshots, or compute forward labels.

## Reviewer No-Hit Acceptance and Downstream Impact Workflows

Reviewer no-hit source coverage acceptance artifacts are report-only supporting-context records.

They may record reviewer acceptance of source coverage, query windows, no-hit inference limits, and survivorship rationale; create reviewer acceptance templates; validate reviewer-completed no-hit acceptance updates; and expose accepted, needs-review, reviewer-required, and survivorship-rationale-required counts in research-status.

They must not apply PIT approvals, set `APPROVED_FOR_PIT_UNIVERSE`, create approval update CSVs, run PIT review, run export-readiness, run staging, export universe files, write `data/raw` or `data/processed`, mutate active worklists or market cache, run current-candidates, build snapshots, or compute forward labels.

Reviewer no-hit acceptance downstream impact artifacts are report-only downstream context summaries. They may link accepted no-hit context to packet/checklist/policy impact reports and expose context counts in research-status, but they must not change strict checklist behavior or apply approvals.

## First-Batch Reviewer Evidence Completion Plan Workflows

First-batch reviewer evidence completion plan artifacts are report-only reviewer planning artifacts.

They may:

- build a 16-row first-batch planning table for `000001` stock_core and `159915` etf_core;
- preserve lineage to evidence update plan, validator, policy comparison, reviewed no-hit policy comparison, official status packet, enrichment, reviewer no-hit acceptance, and downstream impact artifacts;
- classify missing evidence into reusable symbol-level evidence, date-specific evidence, reviewer no-hit acceptance to-do, survivorship rationale to-do, and metadata completion to-do;
- create a reviewer completion template;
- expose reviewer completion required, no-hit acceptance required, survivorship rationale required, metadata completion required, checklist pass, remaining blocked, clean-review-update, and approval-applied counts in research-status.

They must not:

- apply approvals;
- reject rows;
- set `APPROVED_FOR_PIT_UNIVERSE`;
- set `include_flag=true`;
- set `valid_for_signal_date=true`;
- create clean `review_updates.csv`;
- run PIT review;
- run export-readiness;
- run staging;
- export universe files;
- write `data/raw` or `data/processed`;
- mutate active worklists or market cache;
- run current-candidates;
- build snapshots;
- compute forward labels.

Current first-batch plan state:

```text
plan_id: c630522f235a
stage: FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_NEEDS_REVIEW
row_count: 16
stock_core_row_count: 8
etf_core_row_count: 8
reviewer_completion_required_count: 16
no_hit_acceptance_required_count: 16
survivorship_rationale_required_count: 16
metadata_completion_required_count: 16
checklist_pass_count: 0
remaining_blocked_count: 16
clean_review_updates_created: false
approval_applied: false
```

A reviewer completion template is not a clean review update and must not be fed directly as an applied approval.

## Export-Readiness and Export-Staging Workflows

Export-readiness blocks export when there are no approved rows, evidence is missing, survivorship is unresolved, required universe columns are missing, duplicates exist, or PIT dates are invalid. It must not write `data/raw` or `data/processed`.

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
ingestion_only=true
export_readiness_only=true
staging_only=true
audit_only=true
acceptance_only=true
activation_only=true
evidence_update_plan_only=true
checklist_validation_only=true
policy_profile_comparison_only=true
evidence_packet_only=true
evidence_packet_enrichment_only=true
reviewer_no_hit_acceptance_only=true
downstream_impact_only=true
first_batch_reviewer_completion_plan_only=true
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

Safe parse failures, stale warnings, planning blockers, review evidence blockers, ingestion blockers, profile conflicts, replacement planning context, replacement acceptance context, replacement activation context, evidence update planning context, checklist validation blockers, policy profile comparison blockers, official status evidence packet blockers, reviewer no-hit acceptance blockers, downstream impact blockers, first-batch reviewer completion planning blockers, export-readiness blockers, staging blockers, and worklist blockers should not override later validated paper workflow unless they represent an active blocking error for the current workflow.

## When to Refresh This Document

Refresh when:

- new artifact types are added;
- index/health/status patterns change;
- research-status priority changes;
- diagnostic artifact scoping changes;
- reviewer completion template semantics change;
- accepted PIT universe export semantics are implemented;
- snapshot preparation semantics are implemented;
- real alert delivery or broker integration is introduced.
