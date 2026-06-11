# Historical Replay Training Strategy

> Status: working memory document  
> Last generated: 2026-06-12  
> Permanence: temporary; update when replay schema, training methodology, research-method stack, stock-profile validation, or real buy-review eligibility rules change.

## Purpose

This document defines the core long-term research capability of `quant-replay-system`:

```text
historical replay training for China A-share/ETF advisory.
```

The first usable product is personal/family advisory. The research core must still support institution-grade historical replay, PIT validity, factor universe expansion, broad research-method governance, forward-return evaluation, and stock-level validation before real buy-review eligibility.

## Core Idea

For a historical decision date `T`, the system should behave as if it is living on date `T`:

```text
Only data available at or before T can be used.
Future prices, future universe membership, future ST/delist/suspension state,
future announcements, future financial statements, future news, and future labels are forbidden.
```

Then the system generates a review-only decision:

```text
WATCH
REVIEW_BUY_CANDIDATE
REVIEW_SELL_CANDIDATE
HOLD_REVIEW
NO_ACTION
BLOCKED
```

After the decision is recorded, future real outcomes are joined as labels:

```text
forward return
benchmark-relative return
industry-relative return
max drawdown
max runup
hit / miss / false positive / false negative
```

The labels are used for evaluation and training. They must never leak into the original replay decision.

## Why This Is Different From Simple Backtesting

A simple backtest usually asks:

```text
Did this price/indicator rule make money historically?
```

This project asks:

```text
On historical date T, with only the data actually available then,
would the system have produced a review candidate?
What evidence and factor layers supported it?
What future outcome happened?
Which weights, thresholds, horizons, regimes, and risk rules should be adjusted?
```

This requires:

- PIT universe validity;
- raw document availability;
- factor observation availability;
- event availability;
- company exposure mappings;
- deterministic replay decisions;
- forward-return labels;
- evaluation reports;
- model/version governance;
- stock-level profiles.

## Current Implemented Preparation: v1.27.0 Schema Fixture

As of v1.27.0, the project has implemented:

```text
replay-substrate-schema-fixture
→ index
→ health
→ status
→ research-status
→ checkpoint doc
```

Latest known state:

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

Interpretation:

```text
schema/fixture contracts exist
≠ real replay can run
≠ forward labels exist
≠ model weights are trained
≠ stock_profile is active
≠ real buy-review eligibility exists
```

## Factor Universe

Do not treat the old 12-factor framework as final.

Use:

```text
8-layer taxonomy = primary system skeleton.
12-factor framework = coverage checklist.
Factor universe = expandable and testable set of factors/events.
```

The factor universe should eventually include:

- market price and volume factors;
- fundamental factors;
- company event factors;
- industry supply/demand factors;
- value-chain and commodity factors;
- macro, policy, and liquidity factors;
- capital-market system and supply/demand factors;
- trading behavior and microstructure factors;
- announcement/news/event factors;
- expectation, valuation, and pricing-deviation factors;
- risk and compliance factors.

Each factor must have metadata:

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
available_time policy
version
```

## Research Method Stack

The project should not be reduced to ML/DL/data mining or formulas/weights.

It should use a broad method stack:

```text
data engineering
PIT evidence governance
statistics
econometrics
financial engineering
factor research
event study
causal inference
knowledge graph / industry-chain modeling
NLP / information retrieval / RAG for public documents
data mining
machine learning
deep learning
optimization
risk management
portfolio construction
execution and slippage modeling
replay evaluation
explainability
DataOps / MLOps / model governance
```

Use methods according to maturity:

```text
Stage 1: evidence, schema, PIT, deterministic rules, baseline statistics.
Stage 2: factor/event evaluation and simple interpretable models.
Stage 3: ML for weight calibration, feature importance, regimes, and error analysis.
Stage 4: DL/NLP/GNN only after sufficient PIT-valid data and labels exist.
Stage 5: portfolio/risk/execution modeling only after signal and paper evidence exist.
```

No method may bypass PIT validity, source legality, forward-label separation, out-of-sample validation, paper workflow, or human confirmation.

## Core Data Entities

### Raw Document Store

Purpose:

```text
store or reference raw public/reviewed documents with enough metadata for replay audit.
```

Fields:

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

### Source Registry

Purpose:

```text
track source permission, reliability, update frequency, and replay suitability.
```

Fields:

```text
source_id
source_name
source_type
permission_class
free_or_paid
requires_token
requires_login
commercial_use_risk
project_role
recommended_stage
reliability_score
revision_risk
supports_historical_replay
status
```

### Factor Definition

Purpose:

```text
define factor contracts under the 8-layer taxonomy.
```

Fields:

```text
factor_id
layer
second_level
factor_name
impact_path
direction_rule
time_horizon
data_sources
data_availability
lag_days
confidence_default
backtestable
compliance_flag
trade_usage
version
status
```

### Factor Observation

Purpose:

```text
store date-specific factor values for symbols/entities.
```

Fields:

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

### Structured Event

Purpose:

```text
convert announcements/news/policy/industry documents into auditable event records.
```

Fields:

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

### Company Exposure

Purpose:

```text
map companies to industries, products, raw materials, value-chain roles, policies, commodities, regions, and styles.
```

Fields:

```text
symbol
company_name
industry
sector
product_type
raw_material_dependency
customer_industry_exposure
export_ratio
region_exposure
value_chain_role
style_exposure
index_membership
source_id
available_time
revision_id
confidence
```

### Replay Decision

Purpose:

```text
record what the system would have said on date T, before future outcomes are known.
```

Fields:

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

### Forward Return Label

Purpose:

```text
store future outcomes for evaluation after replay decisions exist.
```

Fields:

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

### Training Result

Purpose:

```text
record weights, thresholds, model versions, and metrics.
```

Fields:

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

### Stock Profile

Purpose:

```text
record whether a specific stock has enough validated history to enter real buy-review eligibility.
```

Fields:

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

## Model Structure

The preferred model structure is:

```text
base market model
+ industry/sector model
+ stock-specific calibration model
```

Do not rely only on one stock’s data. A single stock can be too sparse and overfit. The stock-specific profile should calibrate a broader base/industry model.

## Training Stages

### Stage A: Manual Prior Weights

Use interpretable prior weights and rules first.

Do not claim validation.

### Stage B: Historical Replay Calibration

After PIT-valid replay decisions and labels exist, evaluate:

- hit rate;
- average return;
- benchmark-relative return;
- maximum drawdown;
- false positives;
- false negatives;
- payoff ratio;
- horizon stability;
- regime stability.

### Stage C: Regime-Aware Weights

Later, weights may change by:

- bull market;
- bear market;
- sideways market;
- policy-driven market;
- liquidity-driven market;
- industry event regime;
- high-volatility risk regime.

### Stage D: Stock-Level Calibration

Stock-specific profiles should learn:

- which factors matter for this stock;
- which factors are misleading for this stock;
- which horizons work;
- which regimes work;
- which risks veto signals;
- whether paper workflow confirms the replay result.

## Evaluation Must Not Rely on Accuracy Alone

Accuracy is not enough.

Evaluate:

```text
hit rate
average return
median return
max drawdown
max runup
profit/loss ratio
false-positive cost
false-negative opportunity cost
benchmark-relative return
industry-relative return
turnover
slippage sensitivity
sample size
regime robustness
```

A model with lower hit rate but better payoff and drawdown may be superior.

A model with high historical accuracy but weak out-of-sample results is not validated.

## Buy-Review Eligibility Gates

Conceptual ladder:

```text
UNTRAINED_OR_UNVALIDATED:
  WATCH / NO_ACTION / BLOCKED only.

PIT_REPLAY_READY:
  replay can run, but no real buy-review eligibility.

HISTORICAL_REPLAY_VALIDATED:
  paper-only REVIEW_BUY_CANDIDATE may be allowed under strict semantics.

PAPER_VALIDATED:
  REAL_BUY_REVIEW_CANDIDATE may be shown for human review.

HUMAN_CONFIRMED:
  user may manually place an order outside the system.
```

The system must not place the order.

## Minimum One-Stock Prototype Scope

A safe early one-stock prototype should be narrow:

```text
one stock or one ETF
limited date range
LOCAL_CSV data only
accepted PIT universe inputs only
small factor subset
no LLM API calls
no forward labels until replay decisions exist
no weight training until labels exist
no real buy-review eligibility
```

The prototype should prove contracts, not performance.

## Overfitting Controls

Required controls:

- train/test split by time;
- out-of-sample validation;
- benchmark comparison;
- industry comparison;
- regime analysis;
- sample-size warnings;
- corporate action and suspension handling;
- data leakage checks;
- no future information in replay decisions;
- simple baselines such as buy-and-hold, benchmark, and basic technical rules.

## LLM Policy

LLM may eventually help with:

```text
public document parsing
structured event draft extraction
summary for human review
entity matching
translation / normalization
```

LLM must not:

```text
act as deterministic buy/sell logic
claim strategy validation
bypass source permissions
use private or restricted information
create real buy-review eligibility
place orders
```

## Current Next Safe Step

```text
Historical Replay Substrate Readiness Plan Report-Only v0.1
```

Purpose:

- use v1.27.0 schema fixture contracts as context;
- define readiness requirements for real replay;
- remain report-only;
- avoid labels, training, active stock profiles, and buy-review eligibility.
