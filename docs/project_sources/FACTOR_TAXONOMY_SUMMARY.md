# Factor Taxonomy v2.0 Summary

## Why The 8-Layer Framework Is The Main Skeleton

The eight-layer framework is the project skeleton because each layer maps to a distinct engineering boundary: company fundamentals and events, industry-chain economics, macro and policy context, capital-market supply and institutional rules, traded-market confirmation, information propagation, expectation and valuation gaps, and risk/compliance boundaries. These are different data contracts and different failure modes, so they should not be collapsed into a single generic factor list.

The framework is intended for source registration, schema design, event extraction, exposure mapping, factor observation, signal scoring, and compliance gating. It is not a trading recommendation system by itself.

## Why The 12 Factors Are Only A Checklist

The original twelve factors are useful as a coverage checklist, but they overlap too much for direct database design. Macro, liquidity, fiscal policy, industry cycle, commodity prices, events, sentiment, and expectation gaps can double-count the same story if they are stored as peer factors. The eight-layer taxonomy gives cleaner ownership boundaries; the twelve-factor list remains a reminder to check coverage during research design.

## Eight Primary Layers

1. 经营与公司事件层
2. 行业供需与产业链价格层
3. 宏观流动性与政策国际层
4. 资本市场制度与供需层
5. 交易行为与微观结构层
6. 信息披露与舆情传播层
7. 预期、估值与定价偏离层
8. 风险事件与合规边界层

## Data Availability Grades

- A: Public, structured, relatively easy to obtain; suitable for direct factor storage and backtesting.
- B: Public but delayed, scattered, or cleaning-heavy; useful for medium-horizon factors or event confirmation.
- C: Public but highly dispersed; often requires crawling, NLP, or proxy variables.
- D: Not directly obtainable; can only be approximated by low-confidence proxies.
- E: Should not be obtained or legally used; prohibited from live signals.

## Required Cross-Layer Metadata Fields

Every factor or event should carry at least: `factor_id`, `layer`, `second_level`, `factor_name`, `impact_path`, `affected_entities`, `direction_rule`, `time_horizon`, `data_sources`, `data_availability`, `proxy_variables`, `lag_days`, `confidence_default`, `backtestable`, `compliance_flag`, and `trade_usage`.

Additional implementation metadata should include source type, public timestamp, available time, source reliability, revision risk, mapping scope, coverage, permission class, and audit trace.

## Future Table Mapping

- `factor_definition`: canonical definitions for layer, second-level group, factor name, path, direction rule, availability, and usage.
- `factor_observation`: dated observations such as values, changes, z-scores, source ids, lag, and quality flags.
- `event_structured`: extracted events with public time, event type, entities, source tier, confidence, and impact path.
- `company_exposure`: company-to-industry, product, raw-material, geography, export, and supply-chain exposure tags.
- `source_registry`: source name, permission class, update frequency, reliability, and allowed use.
- `signal_score`: structured scores for real impact, market confirmation, sentiment, confidence, and final signal score.
- `compliance_rule`: rule ids, trigger conditions, actions, severity, and audit requirements.

## Use In quant-replay-system

Use the taxonomy as source material for future schema design, feature flags, factor definitions, source governance, and risk/compliance gates. The seed CSV is a starting registry, not executable logic. It can support future migrations, tests, documentation, and offline research tooling after review.

## What Should Not Be Done Yet

- Do not turn any factor into a buy/sell recommendation.
- Do not change signal semantics, advisory labels, or trading behavior from this taxonomy alone.
- Do not use E-grade, restricted, rumor-only, or non-public data as tradable inputs.
- Do not claim strategy performance is validated.
- Do not add broker integration, live trading, automated order placement, message delivery, or external API calls.
- Do not write generated research artifacts into tracked cache or output paths.
