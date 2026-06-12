# Checkpoint and Artifact Governance

> Status: working memory document
> Last generated: 2026-06-11
> Permanence: temporary; update after checkpoint policy, artifact-status semantics, replay/training artifacts, or stock-profile governance changes.

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

Do not refresh Project Source after every small audit. Refresh after accepted milestone/checkpoint/tag or when current stage, next branch, artifact governance, training-core direction, or safety boundary changes.

## Artifact Governance Pattern

Most generated artifact workflows should have:

```text
artifact command
→ index
→ health
→ status
→ research-status integration
```

Future replay/training artifacts should follow the same pattern.

## Active vs Legacy Artifacts

Keep legacy artifacts visible, but do not let them drive active workflow status.

Examples include stale snapshots, old review artifacts, diagnostic reconciliation failures, partial historical backfill rejections, old backfill plans without warmup fields, legacy advisory artifacts missing provenance, stale PIT overlay review artifacts missing newer metadata columns, legacy mixed-demo `etf_core` artifacts, replacement worklist plans that are not accepted active worklists, accepted replacement planning artifacts that are not activated worklists, activated replacement planning artifacts that are not PIT-approved universe inputs, activated evidence update plans that are not clean review updates, checklist validator outputs that are not PIT approvals, policy profile comparison outputs that do not change strict validator defaults, official status evidence packets and enrichment artifacts that are not PIT approvals, reviewer no-hit source coverage acceptance artifacts that are supporting-context only, reviewer no-hit downstream impact artifacts that do not apply approvals, first-batch reviewer evidence completion plan artifacts that are planning context only, first-batch partial completion impact artifacts that only report blocker deltas, material PIT evidence gate closure plan artifacts that are closure plans only, reviewer material evidence fill guidance artifacts that are human-fill guidance only, one-row material evidence fill package artifacts that are context drafts only, one-row checklist-pass candidate preview artifacts that are report-only previews only, and no-hit support context that is not approval-grade evidence without reviewer acceptance.

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
- first-batch partial completion impact dry-runs;
- material gate closure planning diagnostics;
- reviewer material evidence fill guidance dry-runs;
- one-row material evidence fill package dry-runs;
- one-row checklist-pass candidate preview dry-runs;
- historical replay schema dry-runs;
- factor observation fixture dry-runs;
- forward-label fixture dry-runs;
- stock-profile validation fixture dry-runs;
- ignored dry-run files.

## PIT Evidence Checklist Validator Workflows

PIT evidence checklist validator artifacts are evidence-gate reports.

They may evaluate draft or completed update CSV rows against strict stock/ETF evidence checklists, produce missing-evidence matrices, produce approval-candidate previews, and expose checklist pass/block counts in research-status.

They must not apply approvals, set `APPROVED_FOR_PIT_UNIVERSE`, run PIT review, run export-readiness, run staging, export universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, compute forward labels, or create replay/training inputs.

A checklist-pass row is only an approval-candidate preview. It still requires explicit PIT review before any approval artifact exists.

## PIT Evidence Policy Profile Comparison Workflows

Known profiles:

```text
STRICT_PIT
EOD_POST_CLOSE_LOW_BUDGET_PIT
EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT
```

They must not change strict validator default behavior, apply approvals, set `APPROVED_FOR_PIT_UNIVERSE`, create approval update CSVs, run PIT review/export-readiness/staging, export universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, compute forward labels, or create replay/training inputs.

## PIT Official Status Evidence Packet and Enrichment Workflows

PIT official status evidence packet artifacts and enrichment artifacts are evidence-packet reports.

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

They must not treat supporting symbol-level evidence, local EOD cache, or no-hit observations as applied approval-grade evidence without explicit reviewer acceptance and source coverage documentation.

## Reviewer No-Hit Acceptance and Downstream Impact Workflows

Reviewer no-hit source coverage acceptance artifacts are report-only supporting-context records. They may record reviewer acceptance of source coverage, query windows, no-hit inference limits, and survivorship rationale, but they must not apply PIT approvals or create approval update CSVs.

Reviewer no-hit acceptance downstream impact artifacts are report-only downstream context summaries. They may link accepted no-hit context to packet/checklist/policy impact reports and expose context counts in research-status, but they must not change strict checklist behavior or apply approvals.

## First-Batch, Material Closure, Guidance, and One-Row Package Workflows

First-batch reviewer evidence completion plan artifacts, first-batch partial completion impact artifacts, material PIT evidence gate closure plan artifacts, reviewer material evidence fill guidance artifacts, and one-row material evidence fill package artifacts are report-only planning/context artifacts.

They must not:

- apply approvals;
- reject rows;
- set `APPROVED_FOR_PIT_UNIVERSE`;
- set `include_flag=true`;
- set `valid_for_signal_date=true`;
- set `survivorship_bias_resolved=true` unless a later explicit approval-grade workflow and review justify it;
- create clean `review_updates.csv`;
- run PIT review;
- run export-readiness;
- run staging;
- export universe files;
- write `data/raw` or `data/processed`;
- mutate active worklists or market cache;
- run current-candidates;
- build snapshots;
- compute forward labels;
- create replay/training inputs;
- treat metadata-only or context-only completion as material PIT evidence closure.

Previous one-row package state:

```text
package_id: 136cbd739ca1
stage: ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE_CONTEXT_DRAFTED
target: 2024-04-02 / 000001 / stock_core
package_row_count: 1
context_field_drafted_count: 17
material_blocker_closed_count: 0
checklist_pass_candidate_count: 0
remaining_blocked_count: 16
clean_review_updates_created: false
approval_applied: false
```

## One-Row Checklist-Pass Candidate Preview Workflows

One-row checklist-pass candidate preview artifacts are report-only previews for a single target row.

They may:

- assess reusable context fields;
- report strict requirement gaps;
- report whether the row is a checklist-pass candidate preview;
- preserve lineage to one-row material package, reviewer guidance, material gate closure, checklist validator, enrichment, no-hit acceptance, and downstream impact artifacts;
- expose preview counts and strict gaps in research-status.

They must not:

- apply approvals;
- reject rows;
- set `APPROVED_FOR_PIT_UNIVERSE`;
- set `include_flag=true`;
- set `valid_for_signal_date=true`;
- set `survivorship_bias_resolved=true`;
- create clean `review_updates.csv`;
- run PIT review;
- run export-readiness;
- run staging;
- export universe files;
- write `data/raw` or `data/processed`;
- mutate active worklists or market cache;
- run current-candidates;
- build snapshots;
- compute forward labels;
- create replay/training inputs;
- treat context-only preview as approval.

Previous one-row checklist-pass candidate preview state:

```text
preview_id: 3d3bcc2f95cf
stage: ONE_ROW_CHECKLIST_PASS_CANDIDATE_PREVIEW_CONTEXT_ONLY
target: 2024-04-02 / 000001 / stock_core
preview_row_count: 1
reusable_context_field_count: 7
strict_requirement_gap_count: 10
row_checklist_pass_candidate: false
checklist_pass_candidate_count: 0
remaining_blocked_count: 16
clean_review_updates_created: false
approval_applied: false
```

## Historical Replay and Training Artifact Governance

Future replay/training artifacts are research artifacts, not trading approvals.

### Raw Document Store Artifacts

`raw_document_store` and document metadata artifacts may store public/reviewed source references, hashes, timestamps, parser versions, and compliance flags.

They must not:

- commit copyrighted or generated raw corpora to Git;
- bypass paywalls or access restrictions;
- treat raw news as a buy/sell signal;
- skip source permission and available_time checks.

### Factor Definition Artifacts

`factor_definition` artifacts may define taxonomy metadata and factor contracts.

They must not:

- claim alpha validity;
- trigger signal semantics changes by themselves;
- treat fixed 12 factors as exhaustive;
- bypass source legality or backtestability fields.

### Factor Observation Artifacts

`factor_observation` artifacts may store date/entity factor values.

They must not:

- use observations unavailable at decision time;
- include future labels;
- be treated as approved replay input unless PIT-valid and quality-passed;
- be treated as trading signals by themselves.

### Event Structured Artifacts

`event_structured` artifacts may contain extracted events from public documents/news/announcements.

They must not:

- make LLM output deterministic trading logic;
- treat rumors or restricted data as tradeable signals;
- omit source, available_time, parser_version, confidence, and compliance fields;
- directly output BUY/SELL.

### Replay Decision Artifacts

`replay_decision` artifacts may record what the system would have said on historical date T.

They must not:

- use data unavailable at T;
- place orders;
- claim performance before labels/evaluation;
- create paper or real review entries unless explicitly routed through later workflows.

### Forward Return Label Artifacts

`forward_return_label` artifacts may record future outcomes for evaluation.

They must not:

- leak into replay decision generation;
- be computed before valid replay/candidate rows exist;
- be used as proof of live performance;
- ignore benchmark, corporate action, suspension, ST, and quality policies.

### Training Result Artifacts

`training_result` artifacts may record weights, thresholds, model versions, and metrics.

They must not:

- claim production validation without out-of-sample and paper evidence;
- change signal semantics defaults automatically;
- create real buy-review eligibility automatically;
- hide overfitting or data leakage warnings.

### Stock Profile Artifacts

`stock_profile` artifacts may summarize stock-specific validation, factor sensitivity, risk vetoes, and eligibility status.

They must not:

- set `real_buy_review_eligible=true` without explicit validation gates;
- place orders;
- override human confirmation;
- hide missing data, weak sample size, regime dependence, or benchmark underperformance.

## Historical Replay Input Gate Validator Fixture Workflows

The `historical-replay-input-gate-validator-fixture` workflow and its index/health/status/research-status context are report-only fixture artifacts.

They may:

- generate synthetic/manual fixture cases for a future historical replay input gate validator;
- prove blocked-case coverage;
- prove exactly one `REPLAY_INPUT_GATE_PASS_CANDIDATE` fixture case;
- expose fixture counts, safety flags, and overclaim guards;
- appear in research-status as replay/training preparation context.

They must not:

- implement the real validator;
- create active replay input;
- run real replay;
- compute forward labels;
- train model weights;
- create active stock profiles;
- create real buy-review eligibility;
- treat `REPLAY_INPUT_GATE_PASS_CANDIDATE` as `ACTIVE_REPLAY_INPUT_READY`;
- override paper workflow or future validated workflow priority;
- claim strategy performance validation.

Current v1.28.0 known state:

```text
latest_fixture_run_id: c76d6f0c41d6
stage: INPUT_GATE_VALIDATOR_FIXTURE_READY
case_count: 68
blocked_case_count: 67
pass_candidate_case_count: 1
active_ready_case_count: 0
validator_implemented: false
active_replay_input: false
forward_labels_exist: false
weights_trained: false
active_stock_profile_exists: false
real_buy_review_eligible: false
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
first_batch_reviewer_completion_plan_only=true
first_batch_partial_completion_impact_only=true
material_pit_evidence_gate_closure_plan_only=true
reviewer_material_evidence_fill_guidance_only=true
one_row_material_evidence_fill_package_only=true
one_row_checklist_pass_candidate_preview_only=true
historical_replay_design_only=true
factor_definition_only=true
factor_observation_only=true
event_extraction_only=true
forward_label_only=true
training_result_research_only=true
stock_profile_validation_only=true
real_buy_review_eligible=false
```

## Survivorship and Point-in-Time Governance

Universe, fundamental, event, news, factor, replay, and label data must preserve PIT validity.

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

Rows derived from a future universe must keep survivorship-bias warnings until reviewed. Rows cannot be exported into usable current-candidates universe input or replay-training input until export-readiness and export/staging gates confirm required metadata.

## Research-Status Priority Rule

`research-status` should summarize context while preserving later workflow priority.

Safe parse failures, stale warnings, planning blockers, review evidence blockers, ingestion blockers, profile conflicts, replacement planning context, replacement acceptance context, replacement activation context, evidence update planning context, checklist validation blockers, policy profile comparison blockers, official status evidence packet blockers, reviewer no-hit acceptance blockers, downstream impact blockers, first-batch reviewer completion planning blockers, partial completion impact blockers, material gate closure blockers, reviewer guidance blockers, one-row material package blockers, one-row checklist-pass preview blockers, replay schema blockers, factor observation blockers, forward-label blockers, training blockers, stock-profile blockers, export-readiness blockers, staging blockers, and worklist blockers should not override later validated paper workflow unless they represent an active blocking error for the current workflow.
