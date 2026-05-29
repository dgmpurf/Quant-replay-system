# Factor Taxonomy Generation Report

Generated at: 2026-05-29T02:53:23

## Input Files Inspected

- `G:\AICODING\Quantitative Trading\background\quantitative_trading_factors_v2.md`
- `G:\AICODING\Quantitative Trading\background\股价影响因素全景表v2.0.md`
- `G:\AICODING\Quantitative Trading\background\中国事件驱动与产业链量化系统的因子分层框架研究.md`
- `G:\AICODING\Quantitative Trading\background\quantitative_trading_factors_v2.xlsx`

## Excel Sheets Inspected

- `Factors_v2`: rows=22, columns=10
- `Name_Mapping`: rows=9, columns=2

## Row Counts Extracted

- Canonical factor definition rows extracted from `股价影响因素全景表v2.0.md`: 235
- Workbook factor example rows inspected from `Factors_v2`: 21
- Framework second-level source/frequency rows inspected: 49

## Output Paths

- `G:\AICODING\Quantitative Trading\quant-replay-system\docs\project_sources\FACTOR_TAXONOMY_V2_FULL.md`
- `G:\AICODING\Quantitative Trading\quant-replay-system\docs\project_sources\FACTOR_TAXONOMY_SUMMARY.md`
- `G:\AICODING\Quantitative Trading\quant-replay-system\docs\project_sources\factor_definition_seed.csv`
- `G:\AICODING\Quantitative Trading\quant-replay-system\docs\project_sources\factor_taxonomy_generation_report.md`

## Layer Row Counts

- 经营与公司事件层: 30 normalized rows
- 行业供需与产业链价格层: 30 normalized rows
- 宏观流动性与政策国际层: 30 normalized rows
- 资本市场制度与供需层: 25 normalized rows
- 交易行为与微观结构层: 30 normalized rows
- 信息披露与舆情传播层: 30 normalized rows
- 预期、估值与定价偏离层: 30 normalized rows
- 风险事件与合规边界层: 30 normalized rows

## Normalization Assumptions

- The full Chinese v2.0 panorama table is treated as the canonical factor-definition source.
- The workbook source is treated as a smaller example/mapping source, not as the full canonical registry.
- Factor ids are stable ASCII snake_case ids using the canonical layer key and a deterministic per-layer alpha code. The original numeric section, such as `1.1`, is preserved only in `source_section`.
- `data_availability` preserves A/B/C/D/E grades when present; non-grade source values such as internal or institutional concepts become `unknown`.
- Numeric confidence values, lag values, proxy variables, and time horizons are not invented when the source does not provide them.
- Exact second-level matches from the framework source/frequency table are used only to enrich `data_sources`.
- Trade usage is conservative metadata only; it is not a recommendation.

## Fields That Could Not Be Fully Normalized

- `direction_rule` is mostly represented by `impact_path`, so it is recorded as `see impact_path`.
- `time_horizon`, `proxy_variables`, `lag_days`, and `confidence_default` are left blank because the source does not provide stable values for these fields.
- `data_sources` is only populated when exact second-level matches exist in the framework source table.
- Some source rows have multi-grade availability such as `A/B` or `C/D`; these are preserved rather than collapsed.

## Validation Counters

- factor_definition_seed.csv row count: 235
- duplicate factor_id count: 0
- missing required core field counts: `{"factor_id": 0, "factor_name": 0, "layer": 0, "second_level": 0, "source_file": 0, "source_section": 0, "taxonomy_version": 0}`
- missing all-column counts: `{"affected_entities": 0, "ai_role": 0, "backtest_value": 0, "backtestable": 0, "compliance_flag": 0, "confidence_default": 235, "data_availability": 0, "data_sources": 202, "direction_rule": 0, "event_or_factor": 0, "factor_id": 0, "factor_name": 0, "impact_path": 0, "lag_days": 235, "layer": 0, "notes": 0, "proxy_variables": 235, "quantifiability": 0, "second_level": 0, "source_file": 0, "source_section": 0, "taxonomy_version": 0, "time_horizon": 235, "trade_usage": 0}`
- data availability counts: `{"A": 91, "A/B": 23, "A/C": 38, "A/D": 6, "B": 2, "B/C": 8, "B/C/D": 1, "B/D": 7, "C": 30, "C/D": 13, "C/E": 1, "D": 5, "D/E": 1, "E": 3, "unknown": 6}`
- compliance flag counts: `{"illegal": 4, "public_data": 214, "restricted": 3, "rumor_only": 4, "unknown": 10}`
- trade usage counts: `{"factor_signal": 196, "no_trade": 4, "observe_only": 7, "risk_filter": 28}`

## Safety Notes

This generation changed documentation and seed data only. It did not change trading logic, signal semantics, advisory behavior, broker integration, order placement, message delivery, API calls, or market cache contents.

## Next Recommended Task

Add a lightweight factor-taxonomy validation command or test fixture that checks `factor_definition_seed.csv` uniqueness, allowed layers, compliance flag values, trade usage values, and source provenance before any future schema migration consumes it.
