# Checkpoint and Artifact Governance

> Status: working memory document  
> Last generated: 2026-06-04  
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

Examples include stale snapshots, old review artifacts, diagnostic reconciliation failures, partial historical backfill rejections, old backfill plans without warmup fields, legacy advisory artifacts missing provenance, stale PIT overlay review artifacts missing newer metadata columns, legacy mixed-demo `etf_core` artifacts, replacement worklist plans that are not accepted active worklists, accepted replacement planning artifacts that are not activated worklists, activated replacement planning artifacts that are not PIT-approved universe inputs, activated evidence update plans that are not clean review updates, checklist validator outputs that are not PIT approvals, policy profile comparison outputs that do not change strict validator defaults, and official status evidence packets that are not PIT approvals.

## Diagnostic vs Active Artifacts

Diagnostic artifacts should remain visible but not block active workflow unless linked.

Examples:

- synthetic PIT universe metadata support smoke;
- synthetic export-ready diagnostics under `manual_diagnostics`;
- synthetic evidence update apply smoke;
- Codex evidence discovery diagnostics;
- policy profile audit diagnostics;
- official status source access smoke diagnostics;
- ignored dry-run files.

## Plan-Only Workflows

Plan-only workflows include:

- `current-candidates-backfill-plan`
- `current-candidates-backfill-execution-manifest`
- `pit-universe-overlay-plan`
- `universe-profile-split-worklist-plan`
- `reviewed-replacement-worklist-plan`
- `activated-replacement-worklist-evidence-update-plan`
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

## Evidence Completion / Worklist / Ingestion Workflows

Evidence completion helper artifacts, evidence review worklist artifacts, and evidence update ingestion artifacts organize or validate evidence. They must not export universe files, write `data/raw` / `data/processed`, run current-candidates, build snapshots, or compute forward labels.

A clean `review_updates.csv` is not an applied approval; it is a validated input that may be manually passed to the review workflow later.

## Universe Profile and Replacement Workflows

Universe profile policy audit artifacts are governance-only and must not approve/reject rows or mutate worklists.

Split-worklist plan artifacts are planning-only and must not create active replacement worklists.

Reviewed replacement worklist plan, acceptance, and activation artifacts are planning context only. Activation is still not approval, export, or candidate generation.

All replacement-related workflows must preserve lineage to:

```text
legacy worklist
policy audit
split plan
replacement plan
acceptance
activation
```

They must not:

- mutate the active legacy worklist;
- approve PIT rows;
- reject PIT rows;
- export universe files;
- write `data/raw` or `data/processed`;
- run current-candidates;
- build snapshots;
- compute forward labels;
- imply a usable current-candidates universe input exists.

## Activated Replacement Evidence Update Planning Workflows

Activated replacement evidence update plan artifacts are evidence-preparation planning context.

They may:

- create profile-specific evidence worklists for `stock_core`, `etf_core`, and `mixed_demo_core`;
- create profile-specific update templates;
- create first-batch evidence packages;
- create evidence source checklists;
- expose planning counts in research-status.

They must not:

- create clean `review_updates.csv`;
- approve rows;
- reject rows;
- set `valid_for_signal_date=true`;
- set `include_flag=true`;
- treat hints as authoritative PIT evidence;
- export universe files;
- write `data/raw` or `data/processed`;
- run current-candidates;
- build snapshots;
- compute forward labels.

A future Codex-driven evidence discovery workflow may use these packages to search local/public evidence and draft completed update CSVs, but actual approval remains gated by evidence update ingestion, strict checklist validation, policy comparison context, official status evidence packet context, and PIT review.

## PIT Evidence Checklist Validator Workflows

PIT evidence checklist validator artifacts are evidence-gate reports.

They may:

- evaluate draft or completed update CSV rows against strict stock/ETF evidence checklists;
- produce missing-evidence matrices;
- produce approval-candidate previews;
- expose checklist pass/block counts in research-status.

They must not:

- apply approvals;
- set `APPROVED_FOR_PIT_UNIVERSE`;
- run PIT review;
- run export-readiness;
- run staging;
- export universe files;
- write `data/raw` or `data/processed`;
- run current-candidates;
- build snapshots;
- compute forward labels.

A checklist-pass row is only an approval-candidate preview. It still requires explicit PIT review before any approval artifact exists.

## PIT Evidence Policy Profile Comparison Workflows

PIT evidence policy profile comparison artifacts are report-only policy context.

They may:

- compare `STRICT_PIT` with opt-in profiles such as `EOD_POST_CLOSE_LOW_BUDGET_PIT`;
- report relaxed blockers and remaining blockers;
- show whether rows would become approval-candidate previews under a policy profile;
- expose comparison counts in research-status.

They must not:

- change the strict validator default behavior;
- apply approvals;
- set `APPROVED_FOR_PIT_UNIVERSE`;
- create approval update CSVs;
- run PIT review;
- run export-readiness;
- run staging;
- export universe files;
- write `data/raw` or `data/processed`;
- run current-candidates;
- build snapshots;
- compute forward labels.

A policy comparison is not approval and does not make a profile the default.

## PIT Official Status Evidence Packet Workflows

PIT official status evidence packet artifacts are evidence-packet reports.

They may:

- combine source access smoke results, prior evidence discovery diagnostics, local EOD cache context, and official symbol-level sources into per-symbol/per-date packets;
- classify evidence as `STRONG_OFFICIAL_DATE_SPECIFIC`, `SUPPORTING_OFFICIAL_SYMBOL_LEVEL`, `SUPPORTING_LOCAL_EOD_CACHE`, `CONTEXT_ONLY`, or `MISSING`;
- rerun diagnostics-only ingestion, checklist validation, and policy comparison;
- expose evidence packet counts in research-status.

They must not:

- apply approvals;
- set `APPROVED_FOR_PIT_UNIVERSE` as an applied value;
- treat supporting official symbol-level evidence as date-specific proof;
- treat local EOD cache as official date-specific proof;
- run PIT review;
- run export-readiness;
- run staging;
- export universe files;
- write `data/raw` or `data/processed`;
- mutate active worklists;
- mutate market cache;
- run current-candidates;
- build snapshots;
- compute forward labels.

Current official status evidence packet state:

```text
packet_id: 8efabe2ffe62
stage: PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_BLOCKED
strong_official_date_specific_count: 0
supporting_official_symbol_level_count: 16
supporting_local_eod_cache_count: 16
missing_count: 40
checklist_pass_count: 0
blocked_count: 16
```

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

Safe parse failures, stale warnings, planning blockers, review evidence blockers, ingestion blockers, profile conflicts, replacement planning context, replacement acceptance context, replacement activation context, evidence update planning context, checklist validation blockers, policy profile comparison blockers, official status evidence packet blockers, export-readiness blockers, staging blockers, and worklist blockers should not override later validated paper workflow unless they represent an active blocking error for the current workflow.

## When to Refresh This Document

Refresh when:

- new artifact types are added;
- index/health/status patterns change;
- research-status priority changes;
- diagnostic artifact scoping changes;
- official date-specific evidence acquisition semantics are implemented;
- accepted PIT universe export semantics are implemented;
- snapshot preparation semantics are implemented;
- real alert delivery or broker integration is introduced.
