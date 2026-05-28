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

## Index, Health, And Status

Use `calibration-to-signal-semantics-index` to discover local proposal runs:

```cmd
python -m quant_replay_system.cli calibration-to-signal-semantics-index
```

The index scans `outputs/reports/calibration_to_signal_semantics/` and writes:

```text
outputs/reports/calibration_to_signal_semantics/index/
  calibration_to_signal_semantics_index.csv
  calibration_to_signal_semantics_index_report.md
  metadata.json
```

Index rows include the proposal run id, status, calibration run count, observed review/watch/blocked counts, `defaults_changed`, proposal categories, report path, summary CSV path, proposals CSV path, metadata path, and created time.

Use `calibration-to-signal-semantics-health` to check proposal artifact completeness and safety boundaries:

```cmd
python -m quant_replay_system.cli calibration-to-signal-semantics-health
```

Health checks verify:

- `metadata.json` is readable,
- the markdown report exists and is readable,
- summary and proposals CSV files exist and are readable,
- required fields exist,
- `defaults_changed=false`,
- proposal rows and report retain `REQUIRE_MORE_EVIDENCE`,
- proposal rows and report retain `DO_NOT_EXPAND_BUY_REVIEW_YET`,
- reports do not claim strategy performance validation,
- reports do not claim live or real trading approval,
- safety metadata keeps no-live/no-broker/no-order/no-message/no-LLM/no-API boundaries.

Health artifacts are written under:

```text
outputs/reports/calibration_to_signal_semantics/health/<health_check_id>/
  calibration_to_signal_semantics_health_report.md
  calibration_to_signal_semantics_health_issues.csv
  calibration_to_signal_semantics_health_summary.csv
  metadata.json
```

Use `calibration-to-signal-semantics-status` to summarize the latest proposal:

```cmd
python -m quant_replay_system.cli calibration-to-signal-semantics-status
```

Expected stages include:

- `NO_CALIBRATION_TO_SEMANTICS_PROPOSALS`
- `CALIBRATION_TO_SEMANTICS_PROPOSAL_READY`
- `CALIBRATION_TO_SEMANTICS_NEEDS_MORE_EVIDENCE`
- `CALIBRATION_TO_SEMANTICS_HEALTH_WARN`
- `CALIBRATION_TO_SEMANTICS_FAILED`

For the current v0.1 proposal shape, the expected stage is usually `CALIBRATION_TO_SEMANTICS_NEEDS_MORE_EVIDENCE`, with next action: keep current defaults, consider WATCH expansion only after more evidence, and do not expand BUY review yet.

## Research Status Integration

`research-status` includes the latest `calibration-to-signal-semantics-status` as proposal/design context. The unified dashboard exports:

- `latest_calibration_to_signal_semantics_proposal_run_id`
- `calibration_to_signal_semantics_status`
- `calibration_to_signal_semantics_stage`
- `calibration_to_signal_semantics_health_status`
- `calibration_to_signal_semantics_defaults_changed`
- `calibration_to_signal_semantics_proposal_categories`
- `calibration_to_signal_semantics_calibration_run_count`
- observed `REVIEW_BUY_CANDIDATE`, `WATCH`, and `BLOCKED` counts
- `calibration_to_signal_semantics_report_path`
- `calibration_to_signal_semantics_next_action`

This dashboard context is not strategy validation and does not approve threshold changes. `KEEP_CURRENT_DEFAULTS`, `DO_NOT_EXPAND_BUY_REVIEW_YET`, and `REQUIRE_MORE_EVIDENCE` remain conservative proposal outputs. `defaults_changed` must remain `false`; if it is `true`, `research-status` treats it as actionable because this report is proposal-only and must not mutate config.

Later workflow stages such as current-candidates, signal semantics, signal advisory, single-symbol advisory, advisory conversation, market-update handoff, and paper workflow keep priority for the final `workflow_stage`. Proposal fields remain visible for audit.

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
