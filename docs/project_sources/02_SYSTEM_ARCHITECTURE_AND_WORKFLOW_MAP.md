# System Architecture and Workflow Map

> Status: working memory document
> Last generated: 2026-06-12
> Permanence: temporary; update after major architecture, workflow, replay, factor, method-stack, or data-contract additions.

## High-Level Architecture

```text
Data Sources
  ├─ LOCAL_CSV
  ├─ AKShare optional
  ├─ BaoStock optional
  ├─ future Tushare optional
  ├─ public official announcement metadata
  ├─ future public news/event sources
  ├─ future public macro/industry sources
  └─ paid vendors only as future backups

Raw Artifacts and Document Store
  ├─ data/raw/<SOURCE>/<dataset>/<run_id>/
  ├─ raw_document_store
  ├─ source_registry
  └─ document_metadata with available_time / source_hash / parser_version

Local Caches
  ├─ data/cache/market/daily_bars.csv
  ├─ future fundamental caches
  ├─ future announcement/event caches
  ├─ future macro/industry caches
  └─ future factor_observation caches

Quality, Policy, and PIT Gates
  ├─ data-source-health
  ├─ market-cache-preflight
  ├─ market-cache-compare
  ├─ market-source-policy
  ├─ data-quality
  ├─ snapshot-quality
  ├─ point-in-time universe gates
  ├─ source permission gates
  └─ survivorship / available_time gates

Taxonomy and Factor/Event Layer
  ├─ factor_definition
  ├─ factor_observation
  ├─ event_structured
  ├─ company_exposure
  ├─ compliance_rule
  └─ source_registry

Research Method Stack Layer
  ├─ statistics / econometrics
  ├─ financial engineering
  ├─ factor research
  ├─ event study
  ├─ causal inference
  ├─ knowledge graph / industry-chain modeling
  ├─ NLP / IR / RAG for public documents
  ├─ data mining
  ├─ ML / DL
  ├─ optimization
  ├─ risk / portfolio / execution modeling
  └─ DataOps / MLOps / model governance

Candidate and Signal Layer
  ├─ current-candidates
  ├─ signal-semantics
  ├─ signal-advisory
  ├─ single-symbol-advisory
  ├─ question-style answer
  └─ advisory-conversation

Historical Replay and Training Layer
  ├─ replay_universe_input
  ├─ historical_replay_input_gate_validator_fixture
  ├─ future historical_replay_input_gate_validator
  ├─ replay_decision
  ├─ replay_evidence_bundle
  ├─ forward_return_label
  ├─ benchmark_label
  ├─ training_result
  ├─ model_version
  ├─ evaluation_report
  └─ stock_profile

Paper and Personal Advisory Layer
  ├─ current-to-paper
  ├─ current-to-paper-review
  ├─ paper-daily
  ├─ paper outcome history
  ├─ personal/family daily advisory report
  └─ real buy-review eligibility only after validation

Dashboards and Status
  ├─ index / health / status for most artifacts
  └─ unified research-status
```

## Established Design Pattern

Important modules follow:

```text
artifact-producing command
→ index
→ health
→ status
→ research-status integration
→ checkpoint doc
```

Replay/training modules should follow the same pattern, but they must remain non-active until explicit gates are satisfied.

## Completed Workflow Chains

### Market Data to Candidate Snapshot

```text
market data source
→ raw artifact
→ market cache
→ reviewed export
→ data-pipeline
→ data-quality
→ snapshot-quality
→ current-candidates
```

### Candidate to Paper Workflow

```text
current-candidates
→ current-to-paper
→ current-to-paper-review
→ WATCH_ONLY review
→ paper-daily
→ paper-workflow-status
→ research-status
```

### PIT Evidence Preparation Chain

```text
market cache coverage
→ current-candidates-backfill-plan
→ warmup-aware plan
→ execution manifest
→ PIT universe overlay plan/template
→ PIT universe overlay review workflow
→ PIT universe export-readiness
→ PIT universe evidence completion helper
→ PIT universe required metadata support
→ guarded PIT universe export staging
→ PIT universe evidence review worklist
→ PIT universe evidence update ingestion
→ universe profile policy audit
→ universe profile split-worklist plan
→ reviewed replacement worklist plan
→ reviewed replacement worklist acceptance
→ reviewed replacement worklist activation
→ activated replacement worklist evidence update plan
→ diagnostics evidence discovery / gap closure
→ strict PIT evidence checklist
→ pit-evidence-checklist-validator
→ PIT evidence policy profile comparison
→ PIT official status evidence packet
→ official status evidence packet enrichment
→ reviewer no-hit source coverage acceptance
→ reviewer no-hit acceptance downstream impact
→ first-batch reviewer evidence completion plan
→ first-batch partial completion impact
→ material PIT evidence gate closure plan
→ reviewer material evidence fill guidance
→ one-row material evidence fill package
→ one-row checklist-pass candidate preview
→ reviewer-supplied material evidence fixture audit
```

PIT evidence artifacts are not replay-ready input unless later explicit approval/export gates make them usable.

### Replay Substrate Schema Fixture Chain

Completed as of v1.27.0:

```text
historical replay training substrate architecture audit
→ replay-substrate-schema-fixture
→ replay-substrate-schema-fixture-index
→ replay-substrate-schema-fixture-health
→ replay-substrate-schema-fixture-status
→ research-status integration
→ docs/release_checkpoint_v1.27.0.md
```

Current known replay-substrate fixture state:

```text
fixture_id: 5f9a393ce90d
stage: REPLAY_SUBSTRATE_SCHEMA_FIXTURE_READY
status: PASS
health_status: PASS
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
schema/fixture contracts exist
≠ real replay input exists
≠ forward labels exist
≠ weights are trained
≠ active stock_profile exists
≠ real buy-review eligibility exists
```

### Historical Replay Input Gate Validator Fixture Chain

Completed as of v1.28.0:

```text
historical replay input gate validator readiness/design diagnostics
→ historical-replay-input-gate-validator-fixture
→ historical-replay-input-gate-validator-fixture-index
→ historical-replay-input-gate-validator-fixture-health
→ historical-replay-input-gate-validator-fixture-status
→ research-status integration
→ docs/release_checkpoint_v1.28.0.md
→ SOURCE_UPDATE_NOTES_v1_28_0.md
```

Current known input gate validator fixture state:

```text
latest_fixture_run_id: c76d6f0c41d6
stage: INPUT_GATE_VALIDATOR_FIXTURE_READY
health: PASS
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

Meaning:

```text
fixture cases exist for future validator testing
≠ real validator exists
≠ active replay input exists
≠ real replay can run
≠ forward labels exist
≠ weights are trained
≠ active stock_profile exists
≠ real buy-review eligibility exists
```

## Target Historical Replay Training Chain

Future target workflow:

```text
accepted PIT universe input
→ per-date replay universe
→ per-date market/fundamental/event availability cut
→ factor_observation build
→ event_structured build
→ company_exposure linkage
→ deterministic replay decision
→ replay evidence bundle
→ forward_return_label build
→ benchmark-relative label build
→ evaluation report
→ training/calibration run
→ model_version and parameter set
→ stock_profile update
→ paper workflow validation
→ real buy-review eligibility only after paper validation
```

This chain must not run until earlier gates are satisfied.

## Stock-Level Validation Chain

Future stock-level validation should follow:

```text
stock universe eligibility
→ data coverage audit
→ factor exposure coverage
→ replay coverage by date range and regime
→ forward-label coverage
→ in-sample training
→ out-of-sample validation
→ benchmark comparison
→ error analysis
→ paper workflow observation
→ stock_profile status
```

A stock profile is not an approval to trade. It only determines whether real buy-review candidates may be shown later.

## Important Data Contracts

### Current-Candidates Universe Input Fields

A usable universe input for `current-candidates` requires:

```text
as_of_date
symbol
name
instrument_type
exchange
listed_date
delisted_date
is_active
is_st
is_suspended
industry
min_lot
t_plus_rule
available_time
revision_id
source
```

### Replay Substrate Fixture Entities

The v1.27.0 schema fixture covers 14 entities:

```text
source_registry
raw_document_store
factor_definition
factor_observation
event_structured
company_exposure
replay_decision
replay_evidence_bundle
forward_return_label
benchmark_label
training_result
model_version
evaluation_report
stock_profile
```

In v1.27.0, later-stage entities such as `forward_return_label`, `training_result`, `evaluation_report`, and `stock_profile` are schema-only / blocked / non-active. They do not imply readiness.

### Historical Replay Input Gate Validator Fixture Status Fields

The v1.28.0 fixture workflow reports a future-validator test fixture context, not a real replay input. Important fields include:

```text
fixture_run_id
workflow_stage
case_count
blocked_case_count
pass_candidate_case_count
active_ready_case_count
validation_issue_count
overclaim_guard_pass_count
overclaim_guard_total_count
validator_implemented=false
active_replay_input=false
forward_labels_exist=false
weights_trained=false
active_stock_profile_exists=false
real_buy_review_eligible=false
report_only=true
diagnostic_only=true
```

`REPLAY_INPUT_GATE_PASS_CANDIDATE` remains a fixture status only. It must not be treated as `ACTIVE_REPLAY_INPUT_READY`.

### Raw Document Store Fields

Future historical document/news/announcement records should include:

```text
document_id
source_id
source_name
source_type
permission_class
url_or_file_ref
title
body_or_text_ref
event_date
publish_time
available_time
fetch_time
source_hash
language
parser_version
revision_id
raw_artifact_path
manual_review_required
compliance_flag
```

### Factor Definition Fields

Future `factor_definition` rows should include:

```text
factor_id
layer
second_level
factor_name
impact_path
affected_entities
direction_rule
time_horizon
data_sources
data_availability
proxy_variables
lag_days
confidence_default
backtestable
compliance_flag
trade_usage
version
status
```

### Factor Observation Fields

Future `factor_observation` rows should include:

```text
as_of_date
symbol_or_entity
factor_id
value
normalized_value
z_score
change_pct
window
available_time
source_id
source_hash
revision_id
quality_status
pit_valid
```

### Structured Event Fields

Future `event_structured` rows should include:

```text
event_id
document_id
event_time_public
available_time
source_tier
source_name
event_type
layer
second_level
impact_path
direction
magnitude_hint
time_horizon
company_candidates
industry_tags
commodity_tags
region_tags
confidence_raw
legality_flag
parser_version
manual_review_required
```

### Replay Decision Fields

Future `replay_decision` rows should include:

```text
replay_id
as_of_date
symbol
model_version
universe_version
factor_snapshot_id
event_snapshot_id
signal_label
score_components
risk_flags
blocked_reasons
evidence_bundle_id
manual_review_required
created_at
llm_api_called=false
approval_applied=false
order_placed=false
```

### Forward Return Label Fields

Future `forward_return_label` rows should include:

```text
as_of_date
symbol
horizon_days
entry_price_basis
exit_price_basis
forward_return
benchmark_return
industry_return
excess_return
max_drawdown
max_runup
hit_label
risk_adjusted_label
corporate_action_adjustment_policy
quality_status
```

### Training Result Fields

Future `training_result` rows should include:

```text
training_run_id
model_version
train_start_date
train_end_date
test_start_date
test_end_date
symbols
factor_set_version
label_horizons
objective
parameters
metrics
benchmark_metrics
overfit_checks
known_limitations
approval_status=research_only
```

### Stock Profile Fields

Future `stock_profile` rows should include:

```text
symbol
profile_version
instrument_type
coverage_status
training_status
paper_status
real_buy_review_eligible=false
validated_signal_types
validated_horizons
factor_sensitivities
risk_vetoes
best_regimes
bad_regimes
benchmark_comparison
error_summary
last_reviewed_at
reviewer
```

## PIT Evidence and Reviewer Context Contracts

PIT checklist validator outputs are gate reports, not approvals. A checklist-pass row is only an approval-candidate preview until an explicit PIT review workflow is run.

Known policy profiles:

```text
STRICT_PIT
EOD_POST_CLOSE_LOW_BUDGET_PIT
EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT
```

None of these profiles changes strict defaults, applies approval, runs PIT review, exports universe files, or creates usable current-candidates input.

## Research-Status Integration Rule

Replay-substrate schema fixture context and input gate validator fixture context in research-status must remain preparation context only.

Safe wording:

```text
Replay substrate schema fixture is report-only.
It proves schema/fixture contracts only.
It is not real replay.
It is not forward-label computation.
It is not model training.
It is not stock-profile validation.
It is not real buy-review eligibility.
```

The replay-substrate schema fixture and input gate validator fixture must not override later validated paper workflow or active workflow states.

## Current Next Technical Branch

```text
Real Historical Replay Input Gate Validator Design Preview Report-Only v0.1
```

Purpose:

- consume v1.27/v1.28 fixture contracts as context only;
- design the real historical replay input gate validator as a report-only preview first;
- keep all outputs report-only;
- do not run replay, labels, training, or stock-profile validation.
