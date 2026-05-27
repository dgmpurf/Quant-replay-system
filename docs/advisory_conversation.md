# Local-only Conversational Advisory Facade v0.1

The advisory conversation facade lets a user ask a simple natural-language question and routes it to existing local single-symbol advisory answer artifacts.

It is deterministic and local. It is not an LLM chat system, broker integration, alert delivery workflow, or automated execution layer.

## Purpose

The workflow supports questions such as:

- `000001 现在能不能买？`
- `510300 要不要继续看？`
- `600519 现在该卖吗？`
- `Should I buy 000001?`
- `Should I sell 510300?`

The facade extracts a six-digit local symbol and a simple advisory intent, then calls the existing `single-symbol-advisory` question-style answer flow. It does not classify trading actions independently; advisory labels come from the shared `signal_semantics` policy through the single-symbol advisory result.

Conversation artifacts carry or link the shared signal semantics provenance from the single-symbol answer. `PARSE_FAILED` artifacts still record a conservative `NO_ACTION` semantics boundary so audits can see that no symbol or recommendation was invented. This metadata is local audit evidence only and does not approve trades, send messages, or call LLM/API services.

```text
local question
-> deterministic parser
-> single-symbol-advisory
-> question-style answer
-> advisory conversation report
-> human review / manual confirmation
```

## Deterministic Parser

The v0.1 parser is rule-based:

- Six-digit symbols such as `000001`, `510300`, `600519`, and `688981` are extracted as text.
- Chinese and English keywords are mapped to simple intents:
  - `BUY_REVIEW`: `买`, `能不能买`, `buy`, `should I buy`
  - `SELL_REVIEW`: `卖`, `卖出`, `sell`, `should I sell`
  - `WATCH_REVIEW`: `关注`, `继续看`, `watch`
  - `HOLD_REVIEW`: `持有`, `hold`
  - `GENERAL_REVIEW`: a question with no supported intent
  - `UNKNOWN`: no recognized intent

If no six-digit symbol is found, the status is `PARSE_FAILED`. The system does not invent a symbol or recommendation.

## CLI Usage

Use a local candidates, scored, or signal artifact. The command does not fetch data.

```cmd
python -m quant_replay_system.cli advisory-conversation --question "000001 现在能不能买？" --candidates outputs\reports\current_candidates\2024-05-20_etf_core_f484cd4648\candidates.csv --answer-style detailed
```

English questions use the same deterministic flow:

```cmd
python -m quant_replay_system.cli advisory-conversation --question "Should I sell 510300?" --candidates outputs\reports\current_candidates\2024-05-20_etf_core_f484cd4648\candidates.csv
```

Optional inputs:

- `--scored-dataset <scored_dataset.csv>`
- `--factor-dataset <factor_dataset.csv>`
- `--signals <signals.csv>`
- `--metadata <metadata.json>`
- `--snapshot-manifest <snapshot_manifest.json>`
- `--answer-style concise|detailed`
- `--output-dir <dir>`

## Artifacts

Artifacts are written under:

```text
outputs/reports/advisory_conversation/<conversation_run_id>/
```

Files:

- `advisory_conversation_report.md`
- `advisory_conversation.json`
- `metadata.json`

Health checks validate both local-only conversation safety and semantics provenance. Legacy artifacts without provenance may warn; artifacts with `semantics_auto_order_allowed=true`, an unexpected semantics policy source, live-trading provenance, or broker provenance fail health.

When parsing succeeds, the metadata links to the generated single-symbol advisory answer:

- `linked_advisory_run_id`
- `linked_answer_run_id`
- `linked_answer_markdown_path`

## Index, Health, And Status

Use `advisory-conversation-index` to discover local conversational advisory runs:

```cmd
python -m quant_replay_system.cli advisory-conversation-index
```

The index scans `outputs/reports/advisory_conversation/` and writes:

```text
outputs/reports/advisory_conversation/index/
  advisory_conversation_index.csv
  advisory_conversation_index_report.md
  metadata.json
```

Use `advisory-conversation-health` to check deterministic parser and safety boundaries:

```cmd
python -m quant_replay_system.cli advisory-conversation-health
```

Health checks verify:

- metadata, conversation JSON, and report files exist and are readable,
- required conversation fields are present,
- parsed symbols such as `000001` remain six-digit strings,
- `llm_api_called=false`,
- `external_api_called=false`,
- `no_message_sent=true`,
- `no_live_trading=true`,
- `no_broker_api=true`,
- `auto_order_allowed=false`,
- `PARSE_FAILED` does not invent a symbol or recommendation,
- `NOT_FOUND` does not invent a recommendation,
- demo conversations do not produce real buy/sell guidance,
- linked answer markdown exists when the conversation status is `READY`,
- no delivery metadata is present.

Health artifacts are written under:

```text
outputs/reports/advisory_conversation/health/<health_id>/
  advisory_conversation_health_report.md
  advisory_conversation_health_issues.csv
  advisory_conversation_health_summary.csv
  metadata.json
```

Use `advisory-conversation-status` to summarize the latest conversational advisory run:

```cmd
python -m quant_replay_system.cli advisory-conversation-status
```

The status view reports the latest conversation run id, original question, parsed symbol, parsed intent, advisory action, parser type, health status, linked answer path, workflow stage, and next manual action.

Expected stages include:

- `NO_ADVISORY_CONVERSATION_ARTIFACTS`
- `ADVISORY_CONVERSATION_READY_FOR_REVIEW`
- `ADVISORY_CONVERSATION_PARSE_FAILED`
- `ADVISORY_CONVERSATION_NOT_FOUND`
- `ADVISORY_CONVERSATION_HEALTH_WARN`
- `ADVISORY_CONVERSATION_FAILED`
- `DEMO_ADVISORY_CONVERSATION_VALIDATED`

`PARSE_FAILED` and `NOT_FOUND` remain safe when no recommendation is invented. Demo conversations remain workflow validation only, and the conversation status layer is still local observability, not an LLM, delivery channel, or order-execution workflow.

`research-status` includes the latest advisory conversation status as contextual evidence. It exports the original question, parsed symbol, parsed intent, status/stage/action, health status, parser type, no-LLM/no-message/no-live-trading flags, and linked answer markdown path while preserving later paper workflow priority. A safe `PARSE_FAILED` or `NOT_FOUND` conversation remains visible but does not override a valid paper workflow or invent guidance.

## Safety Boundaries

- The conversation response is not an order.
- Demo answers are not strategy recommendations.
- `PARSE_FAILED` does not invent a symbol or recommendation.
- `NOT_FOUND` does not invent a recommendation.
- No automatic buy or sell execution is implemented.
- No broker API is implemented or invoked.
- No live trading is implemented or invoked.
- No SMS, email, Telegram, WeChat, webhook, or broker message is sent.
- No LLM API or external API is called.
- Manual confirmation remains required.
- `auto_order_allowed=false`.

## Known Limitations

- The parser is deterministic and simple.
- No conversational memory exists.
- No semantic NLP or LLM interpretation exists.
- The command does not fetch current market data.
- Demo artifacts remain `DEMO_ONLY`.
- Non-demo advisory labels require future strategy validation.
- No real alert delivery channel exists.
- No automation or international market support exists yet.

## Future Work

Future versions may add richer local NLP, symbol aliases, conversation history, or LLM-assisted explanation. Those additions should remain behind explicit audit and safety gates: no broker access, no order placement, no secret exposure, no message sending without explicit delivery workflow, and no automatic upgrade from advisory output to execution.
