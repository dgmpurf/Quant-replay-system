# Factor Taxonomy V2 Summary

> Status: working memory document  
> Last generated: 2026-06-11  
> Permanence: temporary; replace if the factor taxonomy, factor-universe policy, or replay-training use changes materially.

## Purpose

This document summarizes the China A-share factor taxonomy sources for use in `quant-replay-system` Project Sources.

The full taxonomy should be treated as a design framework for future factor/event/fundamental/news/replay modules, not as executable trading logic.

## Canonical Rule

Use this priority when sources overlap:

1. `FACTOR_TAXONOMY_V2_CANONICAL.md` or `股价影响因素全景表v2.0.md` is the canonical factor taxonomy.
2. `中国事件驱动与产业链量化系统的因子分层框架研究.md` explains the strategic and China-specific rationale.
3. `FACTOR_TAXONOMY_V2_RAW_EXCEL_EXPORT.md` is a raw Excel-conversion reference.
4. `factor_definition_seed.csv` is an engineering seed, not a trading model.

If canonical and raw export disagree, prefer canonical unless the user explicitly says otherwise.

## Factor Universe Principle

Do not treat fixed 12 factors as final or exhaustive.

Use:

```text
8 primary layers = system skeleton / database primary classification / modeling backbone.
12-factor framework = coverage checklist / explanation aid / reality check.
Factor universe = expandable set of factors, events, proxies, and observations.
```

Future factor coverage can include many more than 12 factors. Each factor must be versioned, sourced, testable, and governed.

## Core Framework

The taxonomy uses 8 primary layers as the system skeleton:

1. 经营与公司事件层
2. 行业供需与产业链价格层
3. 宏观流动性与政策国际层
4. 资本市场制度与供需层
5. 交易行为与微观结构层
6. 信息披露与舆情传播层
7. 预期、估值与定价偏离层
8. 风险事件与合规边界层

The older 12-factor structure should be treated as a coverage checklist, not as the database primary classification.

## Data Availability Grades

| Grade | Meaning | System Use |
|---|---|---|
| A | Public, structured, relatively easy to obtain. | Can enter factor library and backtests after quality checks. |
| B | Public but lagged, fragmented, or requiring cleaning. | Useful for medium-horizon factors or event confirmation. |
| C | Public but highly scattered; needs crawling, NLP, or proxies. | Event-library use with confidence scoring. |
| D | Not directly available; only approximated by proxies. | Low-confidence proxy signal. |
| E | Should not be acquired or cannot legally be used. | Must not enter trading signals. |

## Required Cross-Layer Metadata

Future factor/event records should preserve:

- `factor_id`
- `layer`
- `second_level`
- `factor_name`
- `impact_path`
- `affected_entities`
- `direction_rule`
- `time_horizon`
- `data_sources`
- `data_availability`
- `proxy_variables`
- `lag_days`
- `confidence_default`
- `backtestable`
- `compliance_flag`
- `trade_usage`
- `available_time_policy`
- `source_id`
- `source_hash`
- `revision_id`
- `quality_status`
- `training_status`
- `stock_profile_usage`

These fields align with future tables such as `factor_definition`, `factor_observation`, `event_structured`, `company_exposure`, `source_registry`, `signal_score`, `compliance_rule`, `replay_decision`, `forward_return_label`, `training_result`, and `stock_profile`.

## Future Table Mapping

| Table | Role |
|---|---|
| `factor_definition` | Stable factor definitions and taxonomy metadata. |
| `factor_observation` | Date-specific observed values for factors. |
| `event_structured` | Structured event records extracted from announcements/news. |
| `company_exposure` | Company-to-industry/product/chain exposure mapping. |
| `source_registry` | Source, permission, reliability, and update-frequency governance. |
| `signal_score` | Scores such as real impact, market confirmation, sentiment, and confidence. |
| `compliance_rule` | Risk/compliance rules, including restricted or illegal data gates. |
| `raw_document_store` | Raw or referenced public/reviewed document storage with available_time and hash metadata. |
| `replay_decision` | Historical decision rows produced without future information. |
| `forward_return_label` | Future outcome labels joined only after replay decisions exist. |
| `training_result` | Versioned weights, thresholds, metrics, limitations, and validation status. |
| `stock_profile` | Stock-level validation profile and real buy-review eligibility gate. |

## Signal Score Concept

Single events or factors should not directly output buy/sell decisions.

A future event/factor scoring layer may use separate scores:

- `real_impact`
- `market_confirmation`
- `sentiment`
- `confidence`

A possible formula from the taxonomy is:

```text
signal_score = 0.40 * real_impact
             + 0.30 * market_confirmation
             + 0.10 * sentiment
             + 0.20 * confidence
```

This is a design reference only. It is not currently validated, and it should not override existing `signal_semantics` safety gates.

## Historical Replay Use

In historical replay, taxonomy rows should be used to generate:

```text
factor_definition
→ factor_observation
→ event_structured
→ replay evidence bundles
→ replay decisions
→ evaluation after forward labels are joined
```

Taxonomy rows must not be turned directly into BUY/SELL signals.

Every replay observation must satisfy:

```text
available_time <= replay decision time
source permitted
quality gate passed
revision_id tracked
future labels excluded from decision
```

## Stock-Level Profile Use

For each stock or ETF, the taxonomy should help build a `stock_profile`:

- which factor layers matter;
- which factors are historically useful;
- which factors are misleading;
- what horizons work;
- what market regimes work;
- what risk vetoes apply;
- whether the profile has passed replay and paper validation.

A stock profile is not a trading instruction. It only governs whether real buy-review candidates may be shown later.

## How This Should Enter quant-replay-system

Recommended sequence:

1. Factor taxonomy source normalization.
2. `factor_definition_seed.csv` validation.
3. `source_registry` schema design.
4. `raw_document_store` schema design.
5. `company_exposure` schema design.
6. Fundamental data schema and LOCAL_CSV ingestion.
7. Event schema and LOCAL_CSV ingestion.
8. Event/factor quality gates.
9. Factor observation prototype.
10. Replay decision schema.
11. Forward-return label schema.
12. Training/evaluation schema.
13. Stock profile schema.
14. Advisory context integration.
15. Only later: scoring integration, replay training, and paper validation.

## What Not To Do Yet

Do not:

- turn taxonomy rows into live signals;
- treat 12 factors as final or exhaustive;
- change `signal_semantics` defaults based on taxonomy alone;
- use news sentiment as a direct buy/sell driver;
- use LLM summaries as scoring inputs;
- bypass point-in-time rules;
- ignore source permissions or legality;
- compute forward labels without valid replay/candidate rows;
- train weights without PIT-valid observations and labels;
- create real buy-review eligibility without stock profile and paper validation;
- add broker integration or automated orders;
- treat `manual_confirm_trade` in the taxonomy as current project behavior.

## Free-First Interpretation

The taxonomy mentions paid or institutional sources in some places. Current project policy is free-first:

- prioritize LOCAL_CSV;
- prioritize AKShare/BaoStock/free Tushare where usable;
- use public official data and announcements conservatively;
- paid vendors remain future backups only.

## Current Engineering Use

At the current project stage, this taxonomy should mainly guide:

- future fundamental data schema;
- future event/news schema;
- factor definition registry;
- company exposure mapping;
- raw document metadata;
- risk/compliance fields;
- historical replay design;
- stock-profile validation design;
- advisory context explanations.

It should not yet drive real trading, non-demo buy-review expansion, or automation.
