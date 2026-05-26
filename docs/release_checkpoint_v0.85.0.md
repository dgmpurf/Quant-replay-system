# Release Checkpoint v0.85.0

## Milestone

Local-only Conversational Advisory Facade.

Recommended tag: `v0.85.0`

## Completed Capabilities

- Added a deterministic local conversational advisory facade.
- Added the `advisory-conversation` CLI command.
- Parsed simple Chinese and English advisory questions without LLM or external API calls.
- Extracted six-digit A-share style symbols such as `000001`, `510300`, `600519`, and `688981`.
- Classified simple local intents:
  - `BUY_REVIEW`
  - `SELL_REVIEW`
  - `WATCH_REVIEW`
  - `HOLD_REVIEW`
  - `GENERAL_REVIEW`
  - `UNKNOWN`
- Routed parsed questions into the existing deterministic `single-symbol-advisory` question-style answer flow.
- Preserved `DEMO_ONLY` behavior for demo artifacts.
- Preserved `NOT_FOUND` behavior without invented recommendations when a parsed symbol is absent from the local artifact.
- Added `PARSE_FAILED` behavior when no symbol is found in the question.
- Wrote local conversational artifacts under:

```text
outputs/reports/advisory_conversation/<conversation_run_id>/
```

- Generated:
  - `advisory_conversation_report.md`
  - `advisory_conversation.json`
  - `metadata.json`
- Recorded linked single-symbol answer artifacts when parsing succeeds:
  - `linked_advisory_run_id`
  - `linked_answer_run_id`
  - `linked_answer_markdown_path`
- Preserved safety metadata:
  - `requires_manual_confirmation=true`
  - `auto_order_allowed=false`
  - `no_live_trading=true`
  - `no_broker_api=true`
  - `no_message_sent=true`
  - `llm_api_called=false`
  - `external_api_called=false`

Latest local dry-run evidence:

- `000001 现在能不能买？`
  - parsed_symbol: `000001`
  - parsed_intent: `BUY_REVIEW`
  - status: `READY`
  - advisory_action: `DEMO_ONLY`
- `Should I sell 510300?`
  - parsed_symbol: `510300`
  - parsed_intent: `SELL_REVIEW`
  - status: `READY`
  - advisory_action: `DEMO_ONLY`
- `999999 现在能买吗？`
  - parsed_symbol: `999999`
  - parsed_intent: `BUY_REVIEW`
  - status: `NOT_FOUND`
  - advisory_action: `NO_ACTION`
  - no recommendation invented
- `这个现在能买吗？`
  - parsed_symbol: empty
  - parsed_intent: `BUY_REVIEW`
  - status: `PARSE_FAILED`
  - advisory_action: `NO_ACTION`
  - no symbol or recommendation invented

## Product Vision Alignment

This milestone moves the project closer to the user's desired human-in-the-loop advisory workflow:

```text
User asks a natural question
-> system extracts symbol and intent locally
-> system routes to deterministic advisory artifacts
-> system explains the local advisory result
-> human reviews before any future action
```

The facade is intentionally not an LLM chat system. It keeps the near-term product focused on quantitative research, signal advisory, and human-confirmed execution assistance while preserving a hard boundary from broker integration, message delivery, or automated trading.

## Workflow Impact

The completed workflow chain is:

```text
user question
-> deterministic local parser
-> parsed symbol / parsed intent
-> single-symbol advisory answer
-> local markdown/json artifacts
-> human review / future alert preview
```

The facade reuses existing local advisory semantics. It does not change scoring logic, data source behavior, paper workflow state, or trading state.

## Validation Baseline

- Backend tests: `1096 passed, 2 warnings`
- Quick tests: `987 passed, 109 deselected, 2 warnings`

The warnings are the existing pandas date-format inference warnings in data ingestion/factor dataset tests.

## Safety Guarantees

- The conversational facade is not an LLM chat system.
- Question parsing is deterministic and local.
- No external data fetch is performed.
- No real SMS, email, Telegram, WeChat, webhook, or broker message delivery is implemented.
- No broker API is implemented or invoked.
- No live trading is implemented or invoked.
- No automatic buy or sell execution is implemented.
- Demo outputs remain `DEMO_ONLY`.
- `NOT_FOUND` does not invent recommendations.
- `PARSE_FAILED` does not invent symbols or recommendations.
- Manual confirmation remains required.
- `auto_order_allowed=false`.
- `APPROVED_FOR_PAPER` is not applied.
- Market cache is not mutated by advisory conversation.
- Generated `data/cache`, `data/raw`, `data/processed`, and `outputs` artifacts are ignored and must not be committed.

## Known Limitations

- Parser is simple keyword matching.
- No conversational memory exists.
- No semantic NLP or LLM interpretation exists.
- `--question` is parsed only by simple deterministic rules.
- Demo artifacts remain `DEMO_ONLY`.
- No real alert delivery channel exists.
- No automatic execution exists.
- No international market support exists.

## Recommended Next Engineering Tasks

1. Add advisory-conversation artifact index, health, and status views before integrating conversation context into `research-status`.
2. Add health checks for parser safety, linked answer completeness, no LLM/API calls, no message delivery, and no invented recommendations.
3. Add `research-status` integration after conversation artifact views exist and can distinguish safe `PARSE_FAILED` / `NOT_FOUND` context from actionable artifact failures.
4. Add richer deterministic parser coverage for common Chinese and English phrasing while keeping symbol extraction explicit.
5. Draft safety gates for any future NLP/LLM-assisted review before adding model calls, message delivery, or automation.
