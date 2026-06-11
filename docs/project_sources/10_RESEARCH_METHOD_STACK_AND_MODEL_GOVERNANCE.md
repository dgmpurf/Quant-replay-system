# Research Method Stack and Model Governance

> Status: working memory document  
> Last generated: 2026-06-12  
> Permanence: temporary; update when research methodology, model governance, training methodology, or real buy-review eligibility rules change.

## Purpose

This document clarifies that `quant-replay-system` is not only an ML/DL/data-mining project and not only an algorithm/weight/formula project.

The project requires a broad quantitative research method stack governed by PIT validity, source provenance, replay discipline, forward-label separation, paper workflow, and human confirmation.

## Core Principle

Do not frame the project as:

```text
ML / DL / data mining only
```

Do not frame it as:

```text
algorithms / weights / formulas only
```

The correct frame is:

```text
PIT-valid data and evidence system
+ expandable factor universe
+ event / industry-chain / company exposure understanding
+ statistics / econometrics / financial engineering
+ factor research / event study / causal inference
+ knowledge graph / NLP / IR / RAG
+ data mining / ML / DL
+ optimization / risk / portfolio / execution modeling
+ replay evaluation / explainability / model governance
→ personal/family advisory first
→ institution-grade research core long term
```

## Method Stack

### 1. Data Engineering and Evidence Governance

Purpose:

```text
make the data usable, reproducible, auditable, and point-in-time valid.
```

Methods / concerns:

- source registry;
- raw document store;
- source hash;
- revision ID;
- available_time;
- quality status;
- missing data policy;
- survivorship-bias control;
- ST / suspension / delisting status;
- corporate action adjustment;
- data lineage.

This layer comes before all modeling.

### 2. Statistics

Purpose:

```text
understand distributions, stability, correlations, significance, and sample limits.
```

Methods:

- descriptive statistics;
- rolling mean/variance;
- correlation and rank correlation;
- hypothesis testing;
- distribution and tail analysis;
- bootstrapping;
- confidence intervals;
- sample-size warnings.

Use before ML/DL to avoid blind modeling.

### 3. Econometrics

Purpose:

```text
model time-series, cross-sectional effects, factor exposures, and regime relationships.
```

Methods:

- time-series regression;
- cross-sectional regression;
- panel data models;
- AR / ARIMA-style baselines;
- volatility models;
- cointegration;
- factor exposure regression;
- rolling and walk-forward regressions.

### 4. Financial Engineering

Purpose:

```text
translate financial market mechanics into correct labels, returns, risk, and execution assumptions.
```

Methods / concerns:

- return definitions;
- adjusted prices;
- benchmark-relative returns;
- industry-relative returns;
- drawdown and runup;
- turnover;
- transaction costs;
- T+1 constraints;
- price limits;
- suspension handling;
- liquidity constraints.

### 5. Factor Research

Purpose:

```text
define, observe, evaluate, and govern factor behavior.
```

Methods:

- factor definition;
- factor observation;
- normalization and winsorization;
- z-score / percentile ranks;
- information coefficient;
- factor decay;
- factor turnover;
- factor crowding;
- factor interaction;
- factor stability by regime and industry.

The 8-layer taxonomy is the primary skeleton. The old 12-factor framework is only a coverage checklist.

### 6. Event Study

Purpose:

```text
measure how announcements, news, policies, and company/industry events affect prices.
```

Methods:

- event windows;
- abnormal returns;
- cumulative abnormal returns;
- pre-event runup;
- post-event drift;
- reversal after overreaction;
- event-type grouping;
- event confidence scoring;
- policy and industry event classification.

### 7. Causal Inference

Purpose:

```text
avoid confusing correlation with cause.
```

Methods:

- difference-in-differences;
- matching / propensity score;
- causal forest where appropriate;
- instrumental variables where appropriate;
- counterfactual comparison;
- treatment/control event grouping;
- placebo tests.

Causal inference should inform confidence and model interpretation. It does not automatically create trading permission.

### 8. Knowledge Graph and Industry-Chain Modeling

Purpose:

```text
represent company exposures, upstream/downstream links, commodities, policies, regions, and value-chain transmission.
```

Methods:

- company exposure mapping;
- industry-chain tags;
- product/raw material dependency;
- commodity linkage;
- policy exposure;
- regional exposure;
- graph propagation;
- peer similarity;
- supplier/customer relationship modeling where legal and public.

### 9. NLP / IR / RAG for Public Documents

Purpose:

```text
structure public announcements, financial reports, policy documents, and news into auditable events and context.
```

Allowed roles:

- document classification;
- entity extraction;
- event extraction;
- risk phrase extraction;
- policy target extraction;
- document retrieval;
- evidence bundle summarization for human review;
- translation / normalization.

Disallowed roles:

- LLM says bullish/bearish → direct buy/sell;
- LLM output becomes deterministic trading logic;
- LLM output bypasses source permission;
- LLM output creates real buy-review eligibility.

### 10. Data Mining

Purpose:

```text
discover candidate patterns and anomalies before formal modeling.
```

Methods:

- clustering;
- anomaly detection;
- association rules;
- frequent pattern mining;
- similar historical case retrieval;
- regime clustering;
- outlier and event co-occurrence detection.

Data mining outputs are research leads, not trading signals by themselves.

### 11. Machine Learning

Purpose:

```text
calibrate weights, classify outcomes, discover nonlinear interactions, and support stock-profile validation.
```

Methods:

- logistic regression;
- ridge / lasso;
- decision trees;
- random forest;
- gradient boosting / LightGBM / XGBoost / CatBoost;
- Bayesian models;
- regime classifiers;
- calibrated probabilities.

Preferred sequence:

```text
simple interpretable baselines
→ tree-based models
→ ensemble / regime-aware models
```

ML must not run before PIT-valid observations and labels exist.

### 12. Deep Learning

Purpose:

```text
support text, sequence, graph, or complex nonlinear pattern extraction when simpler methods are insufficient.
```

Potential uses:

- Chinese financial text embeddings;
- announcement/news/document classification;
- sequence models for time-series contexts;
- graph neural networks for industry-chain propagation;
- multimodal or cross-source event embeddings.

Risks:

- sample hunger;
- weak explainability;
- overfitting;
- hidden leakage;
- higher operational cost;
- harder validation.

DL should be later-stage, not the first trading model.

### 13. Optimization

Purpose:

```text
convert signals and risks into constrained decisions.
```

Methods:

- threshold optimization;
- objective selection;
- risk-adjusted scoring;
- portfolio weight optimization;
- turnover constraints;
- drawdown constraints;
- transaction cost constraints.

Optimization must be benchmarked and guarded against overfitting.

### 14. Risk Management

Purpose:

```text
avoid unacceptable losses, hidden exposures, and invalid trades.
```

Methods / controls:

- risk vetoes;
- max drawdown controls;
- stop-review rules;
- liquidity filters;
- ST / suspension / delisting filters;
- industry concentration limits;
- correlation / exposure checks;
- event risk gates;
- compliance gates.

Risk gates can block signals regardless of model score.

### 15. Portfolio Construction

Purpose:

```text
handle multiple signals and existing holdings.
```

Methods:

- position sizing;
- diversification;
- sector constraints;
- exposure balancing;
- cash management;
- benchmark tracking;
- rebalance rules;
- portfolio-level drawdown.

This belongs after signal and paper evidence, not before.

### 16. Execution and Slippage Modeling

Purpose:

```text
estimate whether a signal can be realistically acted on.
```

Methods / concerns:

- T+1 rule;
- limit-up / limit-down;
- open/close/next-day execution assumptions;
- volume participation;
- bid/ask spread where available;
- slippage and fees;
- suspension handling.

The project currently does not place orders.

### 17. Replay Evaluation

Purpose:

```text
evaluate frozen replay decisions after future labels are joined.
```

Metrics:

- hit rate;
- average return;
- median return;
- benchmark-relative return;
- industry-relative return;
- max drawdown;
- max runup;
- profit/loss ratio;
- false-positive cost;
- false-negative opportunity cost;
- turnover;
- slippage sensitivity;
- regime robustness;
- sample size.

Accuracy alone is insufficient.

### 18. Explainability

Purpose:

```text
make decisions reviewable by humans.
```

Methods:

- factor contribution;
- evidence bundle;
- feature importance;
- SHAP-like explanations where appropriate;
- counterfactual notes;
- risk veto explanation;
- peer/industry comparison;
- similar historical cases.

Explainability is required before personal/family advisory becomes trustworthy.

### 19. DataOps / MLOps / Model Governance

Purpose:

```text
make research reproducible and safe to maintain.
```

Required governance:

- dataset version;
- factor version;
- model version;
- parameter version;
- training run ID;
- train/test windows;
- known limitations;
- out-of-sample checks;
- overfit warnings;
- research_only / paper_only / eligible state;
- artifact lineage;
- audit logs.

## Method Gating Rules

No method may bypass these gates:

```text
PIT availability
source permission
quality status
revision tracking
future-label separation
out-of-sample validation
benchmark comparison
paper workflow
human confirmation
```

## Allowed Current Use

At the current stage, methods may be used for:

- schema design;
- fixture design;
- report-only readiness planning;
- factor taxonomy organization;
- evidence governance;
- diagnostic summaries;
- future methodology planning.

## Disallowed Current Use

Do not yet use methods to:

- compute real forward labels;
- train weights;
- optimize thresholds;
- create active stock profiles;
- create real buy-review eligibility;
- change signal semantics;
- generate orders;
- claim performance validation.

## Practical Method Sequence

Recommended long-term sequence:

```text
1. Data/PIT/source governance.
2. Factor and event schema.
3. Replay decision schema.
4. Forward label schema.
5. One-stock LOCAL_CSV replay prototype.
6. Baseline statistics and simple rules.
7. Factor/event evaluation.
8. Forward labels and evaluation reports.
9. Interpretable ML and regime analysis.
10. Stock-profile validation.
11. Paper workflow validation.
12. Only then real buy-review candidate eligibility.
```

## Codex Task Implication

Codex should not be asked to “build the ML system” or “train the model” until prerequisites exist.

Safe task pattern:

```text
read-only audit
→ schema fixture
→ validator
→ index / health / status
→ research-status
→ checkpoint doc
→ readiness plan
→ small LOCAL_CSV prototype
→ only later labels/training/evaluation
```

Codex recommendations are reference only; ChatGPT and the user decide the project path.
