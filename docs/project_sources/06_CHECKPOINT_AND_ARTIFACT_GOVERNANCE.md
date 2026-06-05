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

Examples include stale snapshots, old review artifacts, diagnostic reconciliation failures, partial historical backfill rejections, old backfill plans without warmup fields, legacy advisory artifacts missing provenance, stale PIT overlay review artifacts missing newer metadata columns, legacy mixed-demo `etf_core` artifacts, replacement worklist plans that are not accepted active worklists, accepted replacement planning artifacts that are not activated worklists, activated replacement planning artifacts that are not PIT-approved universe inputs, activated evidence update plans that are not clean review updates, checklist validator outputs that are not PIT approvals, policy profile comparison outputs that do not change strict validator defaults, official status evidence packets and enrichment artifacts that are not PIT approvals, reviewer no-hit source coverage acceptance artifacts that are supporting-context only, reviewer no-hit downstream impact artifacts that do not apply approvals, and no-hit support context that is not approval-grade evidence without reviewer acceptance.

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
- ignored dry-run files.

## Review-Only and Evidence Workflows

PIT universe overlay review artifacts may create statuses such as `NEEDS_MANUAL_REVIEW`, `APPROVED_FOR_PIT_UNIVERSE`, `REJECTED`, and `NEEDS_MORE_EVIDENCE`, but review-only does not mean exported universe input.

Evidence completion helper artifacts, evidence review worklist artifacts, and evidence update ingestion artifacts organize or validate evidence. They must not export universe files, write `data/raw` / `data/processed`, run current-candidates, build snapshots, or compute forward labels.

A clean `review_updates.csv` is not an applied approval; it is a validated input that may be manually passed to the review workflow later.

## Universe Profile and Replacement Workflows

Universe profile policy audit artifacts are governance-only and must not approve/reject rows or mutate worklists.

Split-worklist plan artifacts are planning-only and must not create active replacement worklists.

Reviewed replacement worklist plan, acceptance, and activation artifacts are planning context only. Activation is still not approval, export, or candidate generation.

All replacement-related workflows must preserve lineage and must not mutate the active legacy worklist, approve PIT rows, reject PIT rows, export universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, compute forward labels, or imply a usable current-candidates universe input exists.

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

Current official status evidence packet enrichment state:

```text
enrichment_id: cb5f323d3c8c
source_packet_id: 8efabe2ffe62
stage: PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_ENRICHMENT_BLOCKED
strong_official_same_date_quotation_count: 16
reviewed_no_hit_context_supported_count: 16
reviewer_acceptance_required_count: 16
checklist_pass_count: 0
remaining_blocked_count: 16
```

## Reviewer No-Hit Source Coverage Acceptance Workflows

Reviewer no-hit source coverage acceptance artifacts are report-only supporting-context records.

They may record reviewer acceptance of source coverage, query windows, no-hit inference limits, and survivorship rationale; create reviewer acceptance templates; validate reviewer-completed no-hit acceptance updates; and expose accepted, needs-review, reviewer-required, and survivorship-rationale-required counts in research-status.

They must not apply PIT approvals, set `APPROVED_FOR_PIT_UNIVERSE`, create approval update CSVs, run PIT review/export-readiness/staging, export universe files, write `data/raw` or `data/processed`, mutate active worklists or market cache, run current-candidates, build snapshots, or compute forward labels.

Current reviewer no-hit acceptance state:

```text
acceptance_id: 2e05e4b74794
stage: REVIEWER_NO_HIT_SOURCE_COVERAGE_ACCEPTANCE_NEEDS_REVIEW
row_count: 64
accepted_count: 0
needs_review_count: 64
reviewer_acceptance_required_count: 64
survivorship_rationale_required_count: 16
checklist_pass_count: 0
remaining_blocked_count: 16
```

Accepted no-hit coverage is supporting context only and still does not by itself create checklist-pass rows, PIT approvals, export-ready universe rows, or usable current-candidates input.

## Reviewer No-Hit Acceptance Downstream Impact Workflows

Reviewer no-hit acceptance downstream impact artifacts are report-only downstream context summaries.

They may:

- link accepted no-hit supporting context to packet/checklist/policy context by `signal_date + symbol + universe_name + exception_type`;
- preserve lineage to acceptance, enrichment, packet, policy comparison, and validator artifacts;
- report accepted no-hit context counts and packet context gap reductions;
- report remaining checklist blockers and approval flags;
- expose downstream impact counts in research-status.

They must not:

- apply PIT approvals;
- set `APPROVED_FOR_PIT_UNIVERSE`;
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

Current active downstream impact state:

```text
impact_id: 9e164963455e
stage: REVIEWER_NO_HIT_ACCEPTANCE_DOWNSTREAM_IMPACT_NO_ACCEPTED_CONTEXT
accepted_no_hit_context_count: 0
packet_context_gap_reduced_count: 0
checklist_pass_count: 0
remaining_blocked_count: 16
approval_applied: false
```

Diagnostics fixture downstream impact demonstrates accepted supporting context without approval:

```text
impact_id: 4423bdd3e843
accepted_no_hit_context_count: 4
packet_context_gap_reduced_count: 1
checklist_pass_count: 0
remaining_blocked_count: 16
approval_applied: false
```

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

Safe parse failures, stale warnings, planning blockers, review evidence blockers, ingestion blockers, profile conflicts, replacement planning context, replacement acceptance context, replacement activation context, evidence update planning context, checklist validation blockers, policy profile comparison blockers, official status evidence packet blockers, reviewer no-hit acceptance blockers, downstream impact blockers, export-readiness blockers, staging blockers, and worklist blockers should not override later validated paper workflow unless they represent an active blocking error for the current workflow.

## When to Refresh This Document

Refresh when:

- new artifact types are added;
- index/health/status patterns change;
- research-status priority changes;
- diagnostic artifact scoping changes;
- first-batch reviewer evidence completion planning semantics are implemented;
- accepted PIT universe export semantics are implemented;
- snapshot preparation semantics are implemented;
- real alert delivery or broker integration is introduced.
