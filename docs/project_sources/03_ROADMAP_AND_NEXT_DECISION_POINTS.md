# Roadmap and Next Decision Points

> Status: working memory document
> Last generated: 2026-06-12
> Permanence: temporary; update after each major checkpoint, current-stage change, next-branch change, training-core change, or method-stack change.

## Current Position

The project is a broad local research system with:

- source comparison and market cache;
- reviewed exports and quality gates;
- current-candidates and signal semantics;
- advisory products and paper workflow;
- calibration tooling;
- multi-date backfill planning;
- PIT universe evidence workflows;
- reviewer material evidence guidance and one-row checklist-pass preview;
- reviewer-supplied material evidence fixture audit;
- historical replay training substrate architecture audit;
- replay-substrate-schema-fixture command;
- replay-substrate-schema-fixture index / health / status;
- replay-substrate-schema-fixture research-status integration;
- v1.27.0 checkpoint doc;
- historical-replay-input-gate-validator-fixture command;
- historical-replay-input-gate-validator-fixture index / health / status;
- historical-replay-input-gate-validator-fixture research-status integration;
- v1.28.0 checkpoint doc and SOURCE_UPDATE_NOTES_v1_28_0.md;
- unified `research-status`.

The project is preparing for true historical replay training, but it is not ready to generate real replay decisions, compute forward returns, train weights, create active stock profiles, change non-demo thresholds, or produce validated buy/sell signals.

## Strategic Roadmap Correction

The project should be managed as:

```text
Personal-first product loop
+ institution-grade research core
+ historical replay training substrate
+ expandable factor universe
+ broad quant research method stack
+ stock-level validation before real buy-review
```

PIT evidence work is necessary because historical replay training is invalid if the system can see future information, future universe membership, future ST/delisting/suspension state, future announcements, future labels, or future prices.

However, PIT evidence is not the end goal. It should be driven toward the minimum credible foundation needed for replay training and stock-profile validation.

## v1.27.0 Completed Checkpoint

Checkpoint:

```text
docs/release_checkpoint_v1.27.0.md
```

Completed workflow:

```text
replay-substrate-schema-fixture
→ replay-substrate-schema-fixture-index
→ replay-substrate-schema-fixture-health
→ replay-substrate-schema-fixture-status
→ research-status integration
→ checkpoint doc
```

Latest known state:

```text
fixture_id: 5f9a393ce90d
fixture status: PASS
fixture stage: REPLAY_SUBSTRATE_SCHEMA_FIXTURE_READY
health: PASS
entity_count: 14
validation_issue_count: 0
overclaim_guard_pass_count: 8
overclaim_guard_total_count: 8
active_replay_input: false
forward_labels_exist: false
weights_trained: false
active_stock_profile_exists: false
real_buy_review_eligible: false
```

Meaning:

```text
schema fixture exists
research-status context exists
checkpoint doc exists
real replay does not exist
forward labels do not exist
weights are not trained
active stock profiles do not exist
real buy-review eligibility does not exist
```

## v1.28.0 Completed Checkpoint

Checkpoint:

```text
docs/release_checkpoint_v1.28.0.md
SOURCE_UPDATE_NOTES_v1_28_0.md
```

Completed workflow:

```text
historical-replay-input-gate-validator-fixture
→ historical-replay-input-gate-validator-fixture-index
→ historical-replay-input-gate-validator-fixture-health
→ historical-replay-input-gate-validator-fixture-status
→ research-status integration
→ checkpoint doc
```

Latest known state:

```text
latest_fixture_run_id: c76d6f0c41d6
fixture health: PASS
fixture stage: INPUT_GATE_VALIDATOR_FIXTURE_READY
case_count: 68
blocked_case_count: 67
pass_candidate_case_count: 1
active_ready_case_count: 0
validation_issue_count: 0
validator_implemented: false
active_replay_input: false
forward_labels_exist: false
weights_trained: false
active_stock_profile_exists: false
real_buy_review_eligible: false
research-status final workflow_stage: PAPER_WORKFLOW_READY
```

Meaning:

```text
fixture workflow exists
artifact views exist
research-status context exists
checkpoint doc exists
real validator does not exist
active replay input does not exist
real replay does not exist
forward labels do not exist
weights are not trained
active stock profiles do not exist
real buy-review eligibility does not exist
```

## Current Quantitative Evidence Status

Current evidence is not enough to validate non-demo buy signals.

Known gaps:

- too few dates;
- only 9 symbols in local cache in prior evidence context;
- demo-only current-candidates;
- no accepted PIT universe export;
- no active accepted PIT universe input;
- no generated multi-date current-candidates from accepted PIT universe;
- no real historical replay decision dataset;
- no real factor observation dataset;
- no structured event dataset;
- no forward-return labels;
- no multi-date outcome dataset;
- no training/evaluation dataset;
- no validated stock-level profiles;
- no linked paper outcome history for replay-trained signals;
- no real buy-review eligibility gates implemented as active behavior.

## Current Recommended Next Branch

### Branch: Real Historical Replay Input Gate Validator Design Preview Report-Only v0.1

Purpose:

1. Use v1.27.0 schema fixture and v1.28.0 input gate validator fixture contracts as context only.
2. Design the real historical replay input gate validator as a report-only preview first.
3. Define what real inputs would be checked and how blockers would be surfaced.
4. Define how pass-candidate differs from active replay readiness.
5. Map required entities:
   - source_registry
   - raw_document_store
   - factor_definition
   - factor_observation
   - event_structured
   - company_exposure
   - replay_decision
   - replay_evidence_bundle
   - forward_return_label
   - benchmark_label
   - training_result
   - model_version
   - evaluation_report
   - stock_profile
6. Keep all outputs report-only.

Do not implement real replay in this branch. Do not compute labels, train weights, create stock profiles, or create buy-review eligibility.

## Historical Replay Training Roadmap

### Phase A: Schema and Governance Foundation

Current state:

```text
v1.27.0 schema fixture ready, report-only.
```

Still needed:

- readiness plan;
- input gate validator fixture workflow and views completed as v1.28.0;
- real input gate validator design preview still needed;
- fixture validators as needed;
- accepted PIT universe gate definition;
- real data contracts;
- source registry and raw document store implementation plan;
- factor observation and event structured implementation plan.

### Phase B: One-Stock / One-ETF Replay Prototype, Still Report-Only

Future, not current:

- pick one stock and/or ETF;
- use only accepted PIT universe inputs;
- use LOCAL_CSV for market/fundamental/event examples;
- build dry-run factor observation artifact;
- build dry-run replay decision artifact;
- do not compute forward labels until valid replay decisions exist;
- do not change signal semantics.

### Phase C: Forward Labels and Evaluation

Only after replay decisions exist:

- 5D / 10D / 20D / 60D return labels;
- benchmark-relative labels;
- industry-relative labels;
- maximum drawdown and runup labels;
- label quality reports.

Forward labels are evaluation labels only and must not leak into replay decision generation.

### Phase D: Research Method and Model Training

Only after sufficient PIT-valid observations, replay decisions, and labels exist:

- statistics / econometrics;
- factor research and event study;
- data mining;
- ML / DL where appropriate;
- causal inference where feasible;
- optimization and risk/portfolio methods;
- manual prior weights first;
- simple interpretable models first;
- regime-aware calibration later;
- strict out-of-sample validation;
- no LLM in deterministic scoring logic.

### Phase E: Stock Profile Validation

A stock can move toward real buy-review eligibility only after:

- data coverage is sufficient;
- PIT validity is proven;
- replay decisions exist;
- forward labels exist;
- benchmark comparisons exist;
- out-of-sample performance is not broken;
- paper workflow evidence exists;
- risk vetoes are defined;
- human review remains required.

## Current Do Not Do Yet List

Do not yet:

- use paid APIs as required dependencies;
- parse all news with LLM;
- treat LLM extraction as deterministic scoring logic;
- treat suggested base-universe hints as authoritative PIT evidence;
- treat worklist rows as reviewed evidence;
- treat evidence update ingestion as approval application;
- treat PIT diagnostics, checklist validators, policy comparisons, official evidence packets, reviewer no-hit context, one-row packages, checklist-pass previews, reviewer-supplied fixture audits, or replay-substrate schema fixtures as active replay input;
- export PIT universe input without real approved/export-ready rows;
- write `data/raw` or `data/processed` from PIT staging;
- run current-candidates backfill without reviewed/exported PIT universe rows;
- compute forward returns without valid multi-date candidates or replay decisions;
- train weights without PIT-valid observations and labels;
- create stock-level real buy-review eligibility without paper validation;
- change `signal_semantics` defaults based on synthetic fixtures;
- turn `REVIEW_BUY_CANDIDATE` into orders;
- send real alerts;
- add broker integration.

## Recent Important Checkpoints

Recent milestone direction:

- v1.20.0: reviewer no-hit acceptance downstream impact.
- v1.21.0: first-batch reviewer evidence completion planning.
- v1.22.0: first-batch partial completion impact.
- v1.23.0: material PIT evidence gate closure plan.
- v1.24.0: reviewer material evidence fill guidance.
- v1.25.0: one-row material evidence fill package.
- v1.26.0: one-row checklist-pass candidate preview.
- v1.27.0: replay substrate schema fixture, artifact views, research-status integration, and checkpoint docs.
- v1.28.0: historical replay input gate validator fixture, artifact views, research-status integration, checkpoint docs, and SOURCE_UPDATE_NOTES.

## Source / Commit / Tag Guidance

Source:

```text
Update Source after v1.28.0 because the input gate validator fixture workflow now has command, index, health, status, research-status, checkpoint docs, and SOURCE_UPDATE_NOTES_v1_28_0.md.
```

Commit:

```text
Commit only after reviewing git diff and ensuring generated outputs are not tracked.
Prefer separating project-source refresh commits from code/checkpoint commits.
```

Tag:

```text
Do not tag automatically.
Tag only after user review, clean commits, and explicit request.
```

## What to Ask ChatGPT Next

```text
Review the v1.27.0 source refresh and give me the next Codex prompt for Historical Replay Substrate Readiness Plan Report-Only v0.1.
```
