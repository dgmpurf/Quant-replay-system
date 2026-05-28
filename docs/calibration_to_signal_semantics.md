# Calibration-to-Signal Semantics Profile Proposal Report v0.1

Calibration-to-Signal Semantics Profile Proposal Report compares local advisory profile calibration artifacts against the current `signal_semantics` defaults and writes a read-only proposal report.

It is local and deterministic. It is not strategy validation, non-demo trading approval, live trading, broker integration, order placement, message delivery, an LLM feature, or an external API workflow.

## Purpose

The report helps decide whether calibration evidence is strong enough to refine future non-demo signal semantics profiles:

```text
advisory-profile-calibration artifacts
-> current signal_semantics defaults
-> calibration-to-signal-semantics proposal report
-> human review of future refinement work
```

The v0.1 conclusion is intentionally conservative:

- keep current `signal_semantics` defaults,
- consider expanding `WATCH` semantics before buy-review semantics,
- do not expand `REVIEW_BUY_CANDIDATE` yet,
- require multi-date, broader-symbol, backtest, or paper-review evidence before threshold changes.

## CLI Usage

```cmd
python -m quant_replay_system.cli calibration-to-signal-semantics
```

Optional paths:

```cmd
python -m quant_replay_system.cli calibration-to-signal-semantics --calibration-root outputs\reports\advisory_profile_calibration --semantics-config config\default.yaml --output-dir outputs\reports\calibration_to_signal_semantics
```

The command reads calibration artifacts and the current `signal_semantics` config. It does not write config, does not change thresholds, and does not call the classifier to alter advisory behavior.

## Proposal Categories

The report can emit these proposal categories:

- `KEEP_CURRENT_DEFAULTS`
- `CONSIDER_WATCH_EXPANSION`
- `DO_NOT_EXPAND_BUY_REVIEW_YET`
- `REQUIRE_MORE_EVIDENCE`
- `NEED_MULTI_DATE_VALIDATION`
- `NEED_MORE_SYMBOLS`
- `NEED_BACKTEST_OR_PAPER_EVIDENCE`

These categories are proposal text only. They are not executable strategy settings.

## Inputs Compared

The report compares:

- current `signal_semantics.reviewed_buy_min_score`,
- current `signal_semantics.watch_min_score`,
- conservative/balanced/experimental calibration thresholds,
- action counts from calibration runs,
- demo-only behavior,
- data-quality fail gates,
- snapshot-quality fail gates,
- blocked row behavior.

`final_score` can appear in calibration evidence as a structural threshold input, but it is not treated as strategy evidence by this report.

## Artifacts

Artifacts are written under:

```text
outputs/reports/calibration_to_signal_semantics/<proposal_run_id>/
```

Files:

- `calibration_to_signal_semantics_report.md`
- `calibration_to_signal_semantics_summary.csv`
- `calibration_to_signal_semantics_proposals.csv`
- `metadata.json`

The metadata records `defaults_changed=false` and `signal_semantics_defaults_changed=false`.

## Safety Boundaries

- This is not strategy validation.
- This does not approve non-demo trading.
- `REVIEW_BUY_CANDIDATE` remains human-review-only.
- No automatic BUY/SELL execution is implemented.
- No broker API or live trading is implemented.
- No real message delivery is implemented.
- No LLM/API calls are made.
- Manual confirmation remains required.
- `auto_order_allowed=false`.
- Generated outputs are ignored local diagnostics and must not be committed.

## Known MVP Limitations

- The report reads existing local calibration artifacts only.
- Demo calibration validates workflow safety, not market edge.
- Synthetic fixtures prove rule behavior, not strategy performance.
- It does not run backtests, paper evaluation, or multi-date robustness checks.
- It does not change `signal_semantics` defaults or write executable strategy settings.
- Future non-demo semantics still require evidence collection and explicit review.
