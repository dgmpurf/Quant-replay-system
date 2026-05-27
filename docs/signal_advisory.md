# Signal Advisory Contract and Alert Preview v0.1

Signal Advisory turns a local `current-candidates` artifact into auditable advisory signal artifacts and local alert preview text.

It is not live trading, broker integration, order placement, or message delivery. It does not send SMS, email, Telegram, WeChat, webhooks, or broker messages.

## Purpose

The advisory layer sits between candidate generation and any human or execution action:

```text
current-candidates -> signal-advisory -> local alert preview -> human review
```

The output answers:

- what to watch,
- why it appeared in the candidate artifact,
- when the advisory artifact is valid,
- what would invalidate it,
- which safety flags apply,
- whether manual confirmation is required.

Every signal requires manual confirmation. `auto_order_allowed` is always `false`.

## Semantics Policy

`signal-semantics` provides the deterministic policy contract for mapping candidate or scored rows into advisory labels before those labels are used by broader advisory workflows:

```cmd
python -m quant_replay_system.cli signal-semantics --input outputs\reports\current_candidates\example\candidates.csv --input-type candidates --profile demo
```

`signal-advisory` uses the shared semantics classifier internally, so users do not need to run `signal-semantics` separately before generating signal artifacts. The semantics policy blocks failed risk/data/snapshot rows, forces demo/not-strategy artifacts to `DEMO_ONLY`, and only allows non-demo `REVIEW_BUY_CANDIDATE` / `REVIEW_SELL_CANDIDATE` as structural human-review labels. It never creates orders, paper approvals, broker messages, or real BUY/SELL instructions. See [signal_semantics.md](signal_semantics.md).

Each generated signal row and `metadata.json` now record the shared semantics provenance: policy source, policy version, classifier name, settings profile, semantics action, semantics reason, manual-confirmation flag, auto-order flag, no-live-trading flag, and no-broker flag. This makes the advisory action auditable without turning it into an order or paper approval.

Semantics runs can be discovered and safety-checked with `signal-semantics-index`, `signal-semantics-health`, and `signal-semantics-status`. These views verify demo safety, no-auto-order flags, no live/broker/message metadata, required output columns, leading-zero symbols, and blocked-row reasons before semantics labels are consumed by downstream advisory workflows.

`research-status` also includes `signal-semantics-status` as advisory-policy context before signal advisory. It shows the latest semantics run id, health status, advisory label counts, profile, input path, and report path. Review labels remain manual-review context only, and later signal/paper workflow stages keep priority.

## Contract

Each signal includes:

- `signal_id`
- `signal_run_id`
- `signal_date`
- `decision_date`
- `symbol`
- `name`
- `instrument_type`
- `source_candidate_run_id`
- `selection_profile`
- `demo_mode`
- `not_strategy_recommendation`
- `advisory_action`
- `semantics_policy_source`
- `semantics_policy_version`
- `semantics_classifier`
- `semantics_settings_profile`
- `semantics_action`
- `semantics_reason`
- `semantics_manual_confirmation_required`
- `semantics_auto_order_allowed`
- `semantics_no_live_trading`
- `semantics_no_broker_api`
- `original_score_action`
- `original_candidate_action`
- `final_score`
- `confidence_level`
- `reason_summary`
- `score_breakdown`
- `entry_condition`
- `exit_condition`
- `invalidation_condition`
- `valid_until`
- `risk_notes`
- `data_source_notes`
- `snapshot_manifest_path`
- `candidates_path`
- `requires_manual_confirmation`
- `auto_order_allowed`
- `no_live_trading`
- `no_broker_api`
- `alert_title`
- `alert_body`

Supported advisory actions:

- `WATCH`
- `REVIEW_BUY_CANDIDATE`
- `REVIEW_SELL_CANDIDATE`
- `HOLD_REVIEW`
- `NO_ACTION`
- `BLOCKED`
- `DEMO_ONLY`

These are advisory labels, not orders.

## Demo Inputs

If the source candidate artifact has `selection_profile=demo`, `demo_mode=true`, or `not_strategy_recommendation=true`, generated signals are marked `DEMO_ONLY`.

Demo signals are workflow validation artifacts only:

- they are not strategy recommendations,
- they do not become buy or sell recommendations,
- they require manual confirmation,
- they cannot be auto-ordered,
- they do not change paper review status,
- they do not apply `APPROVED_FOR_PAPER`.

## Artifacts

By default, artifacts are written under:

```text
outputs/reports/signals/<signal_run_id>/
```

Files:

- `signals.csv`
- `signal_alert_preview.md`
- `signal_advisory_report.md`
- `metadata.json`

The alert preview is local text only. No message is sent.

## CLI Usage

Build advisory signals from an explicit current-candidates CSV:

```cmd
python -m quant_replay_system.cli signal-advisory --candidates outputs\reports\current_candidates\2024-05-20_etf_core_f484cd4648\candidates.csv --alert-preview
```

Optional source artifact paths can be supplied explicitly:

```cmd
python -m quant_replay_system.cli signal-advisory --candidates outputs\reports\current_candidates\example\candidates.csv --candidate-report outputs\reports\current_candidates\example\current_candidates_report.md --metadata outputs\reports\current_candidates\example\metadata.json --alert-preview
```

The CLI prints the signal run id, signal count, advisory action counts, artifact paths, and local-only safety statements.

## Single-Symbol Advisory Review

Use `single-symbol-advisory` when the user wants a focused local review of one symbol from existing candidate, scored, or signal artifacts:

```cmd
python -m quant_replay_system.cli single-symbol-advisory --symbol 000001 --candidates outputs\reports\current_candidates\example\candidates.csv --alert-preview
```

The single-symbol workflow preserves symbol strings such as `000001`, returns `NOT_FOUND` when the symbol is absent, and writes report/CSV/JSON/metadata artifacts under `outputs/reports/single_symbol_advisory/<advisory_run_id>/`.

It is still advisory only. Demo rows remain `DEMO_ONLY`, blocked rows remain `BLOCKED`, manual confirmation is required, `auto_order_allowed=false`, and no message is sent.

Repeated single-symbol reviews can be discovered and checked with `single-symbol-advisory-index`, `single-symbol-advisory-health`, and `single-symbol-advisory-status`. These views keep missing-symbol and demo outputs visible without turning them into executable guidance.

## Index, Health, And Status

Use `signal-advisory-index` to discover local advisory runs:

```cmd
python -m quant_replay_system.cli signal-advisory-index
```

The index scans `outputs/reports/signals/` and writes:

```text
outputs/reports/signals/index/
  signal_advisory_index.csv
  signal_advisory_index_report.md
  metadata.json
```

Index rows include shared signal semantics provenance when present: policy source, policy version, classifier, settings profile, semantics action/reason, and semantics safety flags. Legacy artifacts without provenance remain indexable with blank provenance fields and are handled by health as warning context.

Use `signal-advisory-health` to check file completeness and safety boundaries:

```cmd
python -m quant_replay_system.cli signal-advisory-health
```

Health checks verify:

- `metadata.json` is readable,
- `signals.csv` exists and has the required signal contract columns,
- report and alert preview markdown exist,
- symbols such as `000001` keep leading zeros,
- `requires_manual_confirmation=true`,
- `auto_order_allowed=false`,
- `no_live_trading=true`,
- `no_broker_api=true`,
- demo/not-strategy signals remain `DEMO_ONLY` or `WATCH`,
- message delivery is not detected.

Health artifacts are written under:

```text
outputs/reports/signals/health/<health_id>/
  signal_advisory_health_report.md
  signal_advisory_health_issues.csv
  signal_advisory_health_summary.csv
  metadata.json
```

Use `signal-advisory-status` to summarize the latest advisory state:

```cmd
python -m quant_replay_system.cli signal-advisory-status
```

The status view reports the latest signal run, health status, action counts, shared semantics provenance summary, workflow stage, and next manual action. For demo-only runs, the expected stage is `DEMO_SIGNAL_ADVISORY_VALIDATED` and the next action reminds the user to review the local alert preview without treating `DEMO_ONLY` signals as strategy recommendations.

`research-status` also includes the latest signal advisory status as contextual advisory evidence. It exports fields such as `latest_signal_run_id`, `signal_advisory_status`, `signal_advisory_stage`, `signal_health_status`, signal counts, advisory action counts, source current-candidate run id, selection profile, demo flags, and `alert_preview_path`.

Signal advisory context does not approve or send anything. If a later WATCH_ONLY paper workflow already exists, `research-status` keeps the later paper stage as the final workflow stage while still showing the latest advisory run. If signal advisory is the active stage and health fails because a safety boundary is broken, the failure remains actionable.

## Future Alert Delivery

Future SMS, email, Telegram, WeChat, or webhook delivery should consume the generated signal artifacts. Delivery must not change trading state, approve paper trades, create orders, or bypass manual confirmation.

Any future delivery workflow should keep a separate audit trail for:

- which local signal artifact was used,
- who approved delivery,
- what message was previewed,
- whether a message was actually sent,
- whether manual confirmation remained required.

## Known MVP Limitations

- Uses existing current-candidates artifacts only.
- Does not validate strategy profitability or recommendation quality.
- Does not provide an interactive alert UI.
- Does not send messages.
- Does not integrate with brokers.
- Does not create positions, fills, or paper approvals.
- Non-demo advisory labels are structure for future review workflows and still require manual confirmation.
- Index, health, and status views inspect local artifacts only; they do not send alerts or repair broken runs.
