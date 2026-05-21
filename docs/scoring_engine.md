# Score Engine and Candidate Selection v0.1

Score Engine v0.1 consumes the factor dataset and produces explainable component scores, a clipped final score, an action bucket, and score explanation fields.

It does not implement machine learning, industry plugins, live trading, or broker integration.

## Component Scores

All component scores are normalized or clipped to `0-100`.

### `technical_score`

Uses `technical_score_v01` when present. MVP technical helper values are interpreted as directional values centered near zero and converted to a `0-100` style score. Already-normalized values above `10` are used directly.

If `technical_score_v01` is missing, the fallback uses:

- `close > ma20`
- `ma5 > ma20`
- `volume_ratio_20 > 1.2`
- `rsi14` overheat penalty
- `close < ma20` weakness

### `liquidity_score`

Uses:

- `amount`
- `volume`
- `volume_ratio_20`

Missing or zero `volume` / `amount` is penalized.

### `expectation_score_v01`

A simple MVP placeholder from recent benchmark-relative strength:

- `rel_return_5`
- `rel_return_10`
- `rel_return_20`

High RSI reduces the expectation score to avoid rewarding overheated moves too aggressively.

### `risk_penalty`

Uses:

- `risk_precheck_status`
- `is_st`
- `is_suspended`
- `market_data_available`
- `execution_data_available`
- RSI overheat
- low liquidity
- limit-up / limit-down fields

### `reality_score_v01`

Defaults to neutral `50`. This is intentionally a placeholder until real industry/event/reality factors exist.

### `sentiment_score`

Defaults to neutral `50` for MVP.

## Final Score Formula

Default config:

```text
final_score =
  0.35 * reality_score
+ 0.25 * technical_score
+ 0.15 * expectation_score
+ 0.10 * liquidity_score
+ 0.05 * sentiment_score
- 0.25 * risk_penalty
```

`final_score` is clipped to `0-100`.

## Action Mapping

Hard risk override:

- `BLOCKED` if `risk_precheck_status == BLOCK` or a hard risk rule triggers.

Otherwise:

- `final_score < 60`: `NO_TRADE`
- `60 <= final_score < 70`: `OBSERVE`
- `70 <= final_score < 80`: `PAPER_TRADE`
- `80 <= final_score < 90`: `LIVE_CANDIDATE_SMALL`
- `final_score >= 90`: `STRONG_CANDIDATE_REVIEW_REQUIRED`

The live-candidate label is still only a research label. It does not place orders.

## Candidate Selection

`select_candidates(...)`:

- excludes `BLOCKED` rows by default,
- filters by minimum action bucket,
- supports `top_n`,
- supports `min_final_score`,
- sorts by `final_score` descending,
- preserves `score_breakdown` and `score_reason`,
- does not mutate the input DataFrame.

## Known MVP Limitations

- Reality and sentiment are neutral placeholders.
- Risk rules are simple row-level checks, not portfolio-level risk.
- No industry-specific factors are included.
- No model training or learned weights are included.
- Candidate labels are for research workflow staging, not automated trading.
