# Single-Symbol Advisory Review v0.1

Single-Symbol Advisory Review answers a focused local question about one symbol using existing candidate, scored, or signal advisory artifacts.

It is advisory only. It is not an order, paper approval, broker instruction, alert delivery workflow, or automated execution step.

## Purpose

The workflow supports a local human-in-the-loop review question:

```text
symbol + local artifacts -> single-symbol-advisory -> report / CSV / JSON / optional alert preview -> manual review
```

It can help explain:

- whether the symbol appears in the provided local artifact,
- what the source candidate or score action was,
- what the advisory action label is,
- why that label was assigned,
- when the artifact is valid,
- what invalidates it,
- what risk and data-quality caveats apply,
- whether manual confirmation is required.

The answer is constrained by the provided artifact. If the symbol is absent, the workflow returns `NOT_FOUND` and does not invent a recommendation.

## Inputs

For v0.1, provide at least one of:

- `--candidates <candidates.csv>`
- `--scored-dataset <scored_dataset.csv>`
- `--signals <signals.csv>`

Optional context:

- `--factor-dataset <factor_dataset.csv>`
- `--metadata <metadata.json>`
- `--snapshot-manifest <snapshot_manifest.json>`
- `--date <YYYY-MM-DD>`
- `--alert-preview`

Symbol values are treated as text. A symbol such as `000001` remains `000001`.

## Advisory Actions

Supported advisory labels:

- `DEMO_ONLY`
- `WATCH`
- `REVIEW_BUY_CANDIDATE`
- `REVIEW_SELL_CANDIDATE`
- `HOLD_REVIEW`
- `NO_ACTION`
- `BLOCKED`

These labels are not orders.

The shared [signal semantics policy](signal_semantics.md) defines the deterministic conservative mapping from candidate/scored rows to these advisory labels. `single-symbol-advisory` uses that shared classifier internally when row context is available, so question-style answers and advisory-conversation outputs inherit the same policy. Demo rows remain `DEMO_ONLY`, failed risk/data/snapshot rows become `BLOCKED`, and non-demo buy/sell labels remain manual-review candidates rather than instructions.

Single-symbol advisory CSV/JSON/metadata and question-style answer JSON/metadata record the shared semantics provenance. The provenance fields identify `signal_semantics` v0.1, the classifier name, the settings profile, the semantics action/reason, and the semantics safety flags. They support audits and health checks only; they do not approve execution, paper trading, or message delivery.

Demo inputs keep conservative behavior:

- `selection_profile=demo`, `demo_mode=true`, or `not_strategy_recommendation=true` produces `DEMO_ONLY` unless the row is blocked.
- Demo output is workflow validation only.
- Demo output is not strategy advice.
- Manual confirmation is still required.
- `auto_order_allowed=false`.

If the source row is blocked by `risk_precheck_status`, `score_action`, or candidate action, the advisory action is `BLOCKED`.

If the source action is `NO_TRADE`, the advisory action is `NO_ACTION`.

Non-demo structural labels such as `REVIEW_BUY_CANDIDATE` or `REVIEW_SELL_CANDIDATE` are shared semantics labels. `REVIEW_BUY_CANDIDATE` can appear for a non-demo high-score row that passes the conservative semantics gates; `REVIEW_SELL_CANDIDATE` remains explicit-source-only in v0.1. They still require manual confirmation and do not allow auto-order placement.

## Artifacts

Artifacts are written under:

```text
outputs/reports/single_symbol_advisory/<advisory_run_id>/
```

Files:

- `single_symbol_advisory_report.md`
- `single_symbol_advisory.json`
- `single_symbol_advisory.csv`
- `metadata.json`
- `alert_preview.md` when `--alert-preview` is supplied

The alert preview is markdown only. It is not sent to SMS, email, Telegram, WeChat, webhooks, or any broker.

New health checks verify the semantics provenance. Older artifacts without provenance remain readable and may warn as legacy output; artifacts that claim semantics auto-order, live trading, broker access, or an unexpected semantics policy source fail health.

## CLI Usage

Review one symbol from current candidates:

```cmd
python -m quant_replay_system.cli single-symbol-advisory --symbol 000001 --candidates outputs\reports\current_candidates\2024-05-20_etf_core_f484cd4648\candidates.csv --alert-preview
```

Use explicit metadata and scored dataset context:

```cmd
python -m quant_replay_system.cli single-symbol-advisory --symbol 000001 --candidates outputs\reports\current_candidates\example\candidates.csv --scored-dataset outputs\reports\current_candidates\example\scored_dataset.csv --metadata outputs\reports\current_candidates\example\metadata.json --alert-preview
```

The CLI prints the advisory run id, status, symbol, advisory action, artifact paths, and safety flags.

## Question-Style Answer

Use `--question-style` to render a deterministic local answer from the same single-symbol advisory result:

```cmd
python -m quant_replay_system.cli single-symbol-advisory --symbol 000001 --candidates outputs\reports\current_candidates\2024-05-20_etf_core_f484cd4648\candidates.csv --alert-preview --question-style --question "should I buy?"
```

Optional flags:

- `--question "<text>"` stores and echoes the user question.
- `--answer-style concise|detailed` controls how much local context is rendered.
- `--answer-output-dir <dir>` overrides the answer artifact root.

Question-style answers are local rendering artifacts. They do not call an LLM, parse natural language beyond echoing the question, fetch data, send messages, place orders, or connect to brokers.

Artifacts are written under:

```text
outputs/reports/single_symbol_advisory_answer/<answer_run_id>/
  single_symbol_advisory_answer.md
  single_symbol_advisory_answer.json
  metadata.json
```

The answer includes symbol, advisory action, short answer, reason, score/action context, risk notes, data/source caveats, entry and exit considerations, invalidation condition, validity, manual-confirmation requirement, and no-auto-order/no-live/no-broker/no-message safety fields.

Demo answers explicitly remain workflow validation only. A `NOT_FOUND` answer says the symbol cannot be reviewed from the provided local artifact and no recommendation was invented.

### Question-Style Answer Index, Health, And Status

Use `single-symbol-advisory-answer-index` to discover deterministic local answer runs:

```cmd
python -m quant_replay_system.cli single-symbol-advisory-answer-index
```

The answer index scans `outputs/reports/single_symbol_advisory_answer/` and writes:

```text
outputs/reports/single_symbol_advisory_answer/index/
  single_symbol_advisory_answer_index.csv
  single_symbol_advisory_answer_index_report.md
  metadata.json
```

Use `single-symbol-advisory-answer-health` to check answer artifact completeness and safety boundaries:

```cmd
python -m quant_replay_system.cli single-symbol-advisory-answer-health
```

Health checks verify:

- metadata, markdown answer, and JSON answer files exist and are readable,
- required answer fields are present,
- leading-zero symbols such as `000001` remain strings,
- `requires_manual_confirmation=true`,
- `auto_order_allowed=false`,
- `no_live_trading=true`,
- `no_broker_api=true`,
- `no_message_sent=true`,
- `llm_api_called=false`,
- demo answers do not contain real buy/sell instructions,
- `NOT_FOUND` answers do not invent recommendations,
- no message-delivery metadata is present.

Health artifacts are written under:

```text
outputs/reports/single_symbol_advisory_answer/health/<health_id>/
  single_symbol_advisory_answer_health_report.md
  single_symbol_advisory_answer_health_issues.csv
  single_symbol_advisory_answer_health_summary.csv
  metadata.json
```

Use `single-symbol-advisory-answer-status` to summarize the latest question-style answer:

```cmd
python -m quant_replay_system.cli single-symbol-advisory-answer-status
```

The status view reports the latest answer run id, advisory run id, symbol, source status, advisory action, question, answer style, health status, demo flags, markdown answer path, workflow stage, and next manual action.

Expected stages include:

- `NO_SINGLE_SYMBOL_ADVISORY_ANSWER_ARTIFACTS`
- `SINGLE_SYMBOL_ADVISORY_ANSWER_READY_FOR_REVIEW`
- `SINGLE_SYMBOL_ADVISORY_ANSWER_NOT_FOUND`
- `SINGLE_SYMBOL_ADVISORY_ANSWER_HEALTH_WARN`
- `SINGLE_SYMBOL_ADVISORY_ANSWER_FAILED`
- `DEMO_SINGLE_SYMBOL_ADVISORY_ANSWER_VALIDATED`

`NOT_FOUND` remains safe when no recommendation is invented. Demo answers remain workflow validation only, and the answer status layer is still local observability, not message delivery or order execution.

`research-status` includes the latest `single-symbol-advisory-answer-status` as question-style advisory context. The unified dashboard exposes the latest answered symbol, answer action, question, health status, demo safety flags, and markdown answer path while preserving later paper workflow or broader advisory workflow priority. A latest `NOT_FOUND` answer remains visible but does not become a trading recommendation or active blocker when no advice was invented.

For simple user-style questions, `advisory-conversation` provides a deterministic local facade over the same answer workflow. It extracts a six-digit symbol and basic buy/sell/watch/hold intent, then routes to `single-symbol-advisory` and question-style answer artifacts. It is not an LLM chat system and does not fetch data, send messages, or place orders. See [advisory_conversation.md](advisory_conversation.md).

## Index, Health, And Status

Use `single-symbol-advisory-index` to discover local one-symbol review runs:

```cmd
python -m quant_replay_system.cli single-symbol-advisory-index
```

The index scans `outputs/reports/single_symbol_advisory/` and writes:

```text
outputs/reports/single_symbol_advisory/index/
  single_symbol_advisory_index.csv
  single_symbol_advisory_index_report.md
  metadata.json
```

Use `single-symbol-advisory-health` to check artifact completeness and safety boundaries:

```cmd
python -m quant_replay_system.cli single-symbol-advisory-health
```

Health checks verify:

- metadata, JSON, CSV, report, and requested alert preview files exist,
- required advisory fields are present,
- leading-zero symbols such as `000001` remain strings,
- `requires_manual_confirmation=true`,
- `auto_order_allowed=false`,
- `no_live_trading=true`,
- `no_broker_api=true`,
- `no_message_sent=true`,
- demo reviews do not produce real buy or sell guidance,
- `NOT_FOUND` reviews do not invent recommendations.

Health artifacts are written under:

```text
outputs/reports/single_symbol_advisory/health/<health_id>/
  single_symbol_advisory_health_report.md
  single_symbol_advisory_health_issues.csv
  single_symbol_advisory_health_summary.csv
  metadata.json
```

Use `single-symbol-advisory-status` to summarize the latest one-symbol review:

```cmd
python -m quant_replay_system.cli single-symbol-advisory-status
```

The status view reports the latest advisory run id, symbol, status, advisory action, health status, final score, demo flags, alert preview path, workflow stage, and next manual action.

Expected stages include:

- `NO_SINGLE_SYMBOL_ADVISORY_ARTIFACTS`
- `SINGLE_SYMBOL_ADVISORY_READY_FOR_REVIEW`
- `SINGLE_SYMBOL_ADVISORY_NOT_FOUND`
- `SINGLE_SYMBOL_ADVISORY_HEALTH_WARN`
- `SINGLE_SYMBOL_ADVISORY_FAILED`
- `DEMO_SINGLE_SYMBOL_ADVISORY_VALIDATED`

`NOT_FOUND` is safe when no recommendation is invented. Demo reviews remain workflow validation only and should not be treated as strategy recommendations.

`research-status` includes the latest `single-symbol-advisory-status` as advisory context. The unified dashboard exposes the latest reviewed symbol, action, health status, score, demo flags, and alert preview path while preserving later paper workflow or broader signal workflow priority. A latest `NOT_FOUND` review remains visible but does not become a trading recommendation or active blocker when no advice was invented.

## Safety Contract

Every output records:

- `requires_manual_confirmation=true`
- `auto_order_allowed=false`
- `no_live_trading=true`
- `no_broker_api=true`
- `no_message_sent=true`

The workflow does not:

- place orders,
- approve paper trades,
- apply `APPROVED_FOR_PAPER`,
- connect to brokers,
- mutate market cache,
- send messages,
- call network APIs.

## Known MVP Limitations

- Uses local artifacts only.
- Does not fetch market data.
- Does not validate strategy profitability.
- Does not provide natural-language conversation yet.
- Does not provide real alert delivery.
- Demo artifacts produce review-only output and are not strategy recommendations.
- International market semantics are not implemented.
