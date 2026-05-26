# Release Checkpoint v0.86.0

## Milestone

Advisory Conversation Artifact Index / Health / Status.

Recommended tag: `v0.86.0`

## Completed Capabilities

- Added local artifact observability for advisory conversation runs.
- Added CLI commands:
  - `advisory-conversation-index`
  - `advisory-conversation-health`
  - `advisory-conversation-status`
- Indexed deterministic local parsed-question artifacts under:

```text
outputs/reports/advisory_conversation/
```

- Added index fields for:
  - `conversation_run_id`
  - original question
  - parsed symbol
  - parsed intent
  - status
  - advisory action
  - parser type
  - linked advisory run id
  - linked answer run id
  - linked answer markdown path
  - LLM/API and message safety flags
  - report, JSON, and metadata paths
- Added health checks for:
  - readable metadata, conversation JSON, and report files
  - required fields
  - leading-zero symbol preservation, such as `000001`
  - `llm_api_called=false`
  - `external_api_called=false`
  - no message delivery
  - no live trading
  - no broker API
  - `auto_order_allowed=false`
  - safe `PARSE_FAILED` handling without invented symbols or recommendations
  - safe `NOT_FOUND` handling without invented recommendations
  - demo conversation safety, preserving `DEMO_ONLY`
  - linked answer markdown path visibility for `READY` conversations
- Added latest-conversation status summary and workflow stages:
  - `NO_ADVISORY_CONVERSATION_ARTIFACTS`
  - `ADVISORY_CONVERSATION_READY_FOR_REVIEW`
  - `ADVISORY_CONVERSATION_PARSE_FAILED`
  - `ADVISORY_CONVERSATION_NOT_FOUND`
  - `ADVISORY_CONVERSATION_HEALTH_WARN`
  - `ADVISORY_CONVERSATION_FAILED`
  - `DEMO_ADVISORY_CONVERSATION_VALIDATED`

Latest local dry-run evidence:

- Index artifact count: `4`
- Detected conversations:
  - `000001` question parsed successfully as `BUY_REVIEW`, status `READY`, action `DEMO_ONLY`
  - `510300` English sell question parsed as `SELL_REVIEW`, status `READY`, action `DEMO_ONLY`
  - `999999` parsed as `BUY_REVIEW`, status `NOT_FOUND`, action `NO_ACTION`, no recommendation invented
  - no-symbol local buy question returned `PARSE_FAILED`, action `NO_ACTION`, no symbol or recommendation invented
- Health:
  - status: `PASS`
  - issue_count: `0`
  - error_count: `0`
  - warning_count: `0`
- Latest conversation status:
  - workflow_stage: `ADVISORY_CONVERSATION_PARSE_FAILED`
  - parsed_symbol: empty
  - parsed_intent: `BUY_REVIEW`
  - health_status: `PASS`
  - next_manual_action: provide a six-digit local symbol; no symbol or recommendation was invented

## Product Vision Alignment

This checkpoint strengthens the advisory product layer by making conversational advisory artifacts discoverable, safety-checkable, and summarizable before dashboard integration or any future natural-language expansion.

It preserves the project direction:

```text
user question
-> deterministic local parser
-> advisory conversation artifact
-> index / health / status
-> human review
```

The artifact views keep conversational advisory evidence auditable without turning it into execution, message delivery, or LLM-based advice.

## Workflow Impact

The completed workflow chain is:

```text
user question
-> deterministic local parser
-> advisory-conversation artifact
-> advisory-conversation-index / health / status
-> future research-status integration
-> human review / future alert preview
```

The new views make advisory conversation runs ready for future unified dashboard integration. They do not change scoring logic, advisory action classification, data-source behavior, paper workflow state, or trading state.

## Validation Baseline

- Backend tests: `1112 passed, 2 warnings`
- Quick tests: `1003 passed, 109 deselected, 2 warnings`

The warnings are the existing pandas date-format inference warnings in data ingestion/factor dataset tests.

## Safety Guarantees

- Advisory conversation is not an LLM chat system.
- Parser output is deterministic and local.
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
- Market cache is not mutated by advisory conversation artifact views.
- Generated `data/cache`, `data/raw`, `data/processed`, and `outputs` artifacts are ignored and must not be committed.

## Known Limitations

- Parser is simple keyword and symbol matching.
- No conversational memory exists.
- No semantic NLP or LLM interpretation exists.
- No real alert delivery channel exists.
- No automatic execution exists.
- No international market support exists.
- Unified `research-status` integration is not implemented yet.

## Recommended Next Engineering Tasks

1. Integrate `advisory-conversation-status` into unified `research-status`, preserving later paper workflow priority.
2. Treat safe `PARSE_FAILED` and `NOT_FOUND` as visible non-blocking advisory context in the unified dashboard.
3. Add dashboard regression tests for `DEMO_ADVISORY_CONVERSATION_VALIDATED`, `ADVISORY_CONVERSATION_PARSE_FAILED`, and `ADVISORY_CONVERSATION_NOT_FOUND`.
4. Add richer deterministic parser coverage for common Chinese and English phrasing while keeping symbol extraction explicit.
5. Draft safety gates for any future NLP/LLM-assisted review before adding model calls, message delivery, or automation.
