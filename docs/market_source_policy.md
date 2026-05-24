# Market Source Field Reliability Policy v0.1

The market source policy is a machine-readable table of field-level reliability hints for local market data sources.

It does not fetch data, certify data quality, choose a universal trusted vendor, call broker APIs, place orders, or automate execution.

## Purpose

The project now has multiple local market data paths:

- AKShare/Tencent for stock market history
- AKShare/Sina for ETF market history
- BaoStock for stock market history
- LOCAL_CSV and the local market data cache

Route availability and field semantics differ by source, upstream, security type, and field. The policy records the current evidence so downstream workflows can report useful hints without silently changing scoring or source choice.

## Relationship To Other Checks

- `data-source-health` checks whether a route is available.
- `market-cache-compare` checks whether overlapping cached rows agree.
- `market-source-policy` reports which fields are considered reliable, provisional, unavailable, or caveated.
- `market-cache-preflight` applies schema checks, this policy, optional health metadata, and optional comparison before cache ingest.
- `market-daily-update` uses the preflight gate before optional cache ingest in the local update skeleton.
- `data-pipeline`, `data-quality`, and `snapshot-quality` remain required before current-candidates or replay.

## CLI

```cmd
python -m quant_replay_system.cli market-source-policy
```

Artifacts are written under:

```text
outputs/reports/market_source_policy/<policy_report_id>/
```

Files:

- `market_source_policy_report.md`
- `market_source_policy.csv`
- `metadata.json`

## Status Values

- `RELIABLE`: representative local comparisons support this field for the source/upstream/security type.
- `PROVISIONAL`: data is available but lacks enough cross-source comparison evidence.
- `UNKNOWN`: no explicit policy evidence exists.
- `UNAVAILABLE`: the source route did not provide usable rows or fields.
- `UNSTABLE`: the upstream route is known to be unreliable in local diagnostics.
- `DO_NOT_USE`: reserved for explicit future blocks.
- `CAVEAT_FIRST_WINDOW_ROW`: field can differ on the first comparison-window row due to reference/window-boundary semantics.

## Current Policy Summary

AKShare/Tencent stock:

- `open`, `high`, `low`, `close`, `volume`, and `amount` are `RELIABLE` for tested stock cases.
- `amount` requires the raw Tencent turnover extraction path. AKShare's compact `stock_zh_a_hist_tx` DataFrame field named `amount` is volume in hands, not turnover amount.
- `pre_close` is `CAVEAT_FIRST_WINDOW_ROW`.

BaoStock stock:

- `open`, `high`, `low`, `close`, `volume`, and `amount` are `RELIABLE` for tested stock cases.
- `pre_close` is `CAVEAT_FIRST_WINDOW_ROW`.

AKShare/Sina ETF:

- ETF `open`, `high`, `low`, `close`, `volume`, and `amount` are `PROVISIONAL`.
- Current local data exists for `510300` and `159915`, but BaoStock returned 0 rows for those ETF symbols, so second-source comparison is still missing.

BaoStock ETF:

- ETF fields are `UNAVAILABLE` in the current local run.

Eastmoney:

- Stock market fields are marked `UNSTABLE` because local diagnostics found repeated Eastmoney kline endpoint failures.

## Comparison Policy Hints

`market-cache-compare` includes policy hints in its summary, metadata, and markdown report:

- `source_a_field_reliability`
- `source_b_field_reliability`
- `recommended_for_price`
- `recommended_for_volume`
- `recommended_for_amount`
- `amount_sensitive_preferred_source`
- `pre_close_caveat`

These hints do not override comparison PASS/WARN/FAIL, data-quality, or snapshot-quality. They are research data preparation guidance.

## Cache Acceptance Preflight

Use `market-cache-preflight` before `market-cache-ingest` when a workflow needs an explicit acceptance decision:

```cmd
python -m quant_replay_system.cli market-cache-preflight --input data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv --metadata data\raw\AKSHARE_OPTIONAL\market\<run_id>\metadata.json --require-fields close,volume,amount --reference-source BAOSTOCK_OPTIONAL
```

The preflight maps policy statuses as follows:

- `RELIABLE`: passes for required fields.
- `PROVISIONAL`: `WARN_ACCEPT` by default, `REJECT` with strict provisional mode.
- `UNAVAILABLE` or `DO_NOT_USE`: `REJECT` for required fields.
- `UNSTABLE`: warns or rejects according to config.
- `CAVEAT_FIRST_WINDOW_ROW`: reported as a known caveat, not a full source failure by itself.

`market-daily-update` can run this preflight as part of a local update plan. It does not write accepted rows unless `--accept-cache-write` is supplied.

## Known Limitations

- v0.1 policy is evidence-based from a small local representative comparison set.
- ETF reliability remains provisional until another ETF reference source is available.
- The policy does not mutate cached data.
- The policy does not change scoring formulas.
- The policy is not a trading recommendation.
