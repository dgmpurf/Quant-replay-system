# Release Checkpoint v0.87.0

## Milestone

Advisory Conversation Research Status Integration.

Recommended tag: `v0.87.0`

## Completed Capabilities

- Integrated `advisory-conversation-status` into unified `research-status`.
- Added latest user question visibility in the unified dashboard.
- Added parsed symbol and parsed intent visibility.
- Exported advisory conversation status, stage, action, health status, and parser type.
- Exported safety flags for:
  - `llm_api_called`
  - `no_message_sent`
  - `no_live_trading`
  - `no_broker_api`
  - `auto_order_allowed`
- Preserved linked single-symbol answer context through the linked answer path.
- Classified safe `PARSE_FAILED` states as visible but non-blocking when no symbol or recommendation is invented.
- Classified safe `NOT_FOUND` states as visible but non-blocking when no recommendation is invented.
- Preserved later paper workflow priority, so conversational advisory context does not regress an active paper workflow.

Latest local dry-run evidence:

- `advisory-conversation-status`
  - status: `WARN`
  - stage: `ADVISORY_CONVERSATION_PARSE_FAILED`
  - latest conversation run id: `51db61611297`
  - original question: `这个现在能买吗？`
  - parsed symbol: empty
  - parsed intent: `BUY_REVIEW`
  - advisory action: `NO_ACTION`
  - health status: `PASS`
- `research-status`
  - status: `WARN`
  - final workflow stage: `PAPER_WORKFLOW_READY`
  - advisory conversation context visible
  - next action stayed on the WATCH_ONLY paper workflow path

## Product Vision Alignment

This milestone keeps the product on the advisory-first path:

```text
user question
-> deterministic local parser
-> advisory conversation artifact
-> advisory conversation index / health / status
-> research-status
-> human review
```

The user can now see the latest natural-language advisory question context in the unified dashboard without turning that question into an execution instruction, strategy recommendation, message delivery workflow, or LLM-based chat system.

## Workflow Impact

The completed workflow chain is:

```text
user question
-> deterministic local parser
-> advisory-conversation artifact
-> advisory-conversation-index / health / status
-> research-status
-> human review / future alert preview / future delivery channel
```

`research-status` now reports whether the latest local conversational advisory artifact parsed a symbol, which intent was detected, whether the answer path is linked, and whether all local-only safety flags remain intact.

If a later paper workflow is already active, the final dashboard stage stays with that later workflow. In the latest local dry-run, `PAPER_WORKFLOW_READY` remained the final stage even though the latest conversation was a safe `PARSE_FAILED`.

## Validation Baseline

- Backend tests: `1119 passed, 2 warnings`
- Quick tests: `1010 passed, 109 deselected, 2 warnings`

The warnings are the existing pandas date-format inference warnings in data ingestion/factor dataset tests.

## Safety Guarantees

- Advisory conversation is not an LLM chat system.
- The parser is deterministic and local.
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
- Generated `data/cache`, `data/raw`, `data/processed`, and `outputs` artifacts are ignored and must not be committed.

## Known Limitations

- Parser is simple keyword and symbol matching.
- No conversational memory exists.
- No semantic NLP or LLM interpretation exists.
- No real alert delivery channel exists.
- No automatic execution exists.
- No international market support exists.
- This is dashboard observability only, not strategy validation.

## Recommended Next Engineering Tasks

1. Add richer deterministic parser fixtures for common Chinese and English advisory phrasing while preserving explicit six-digit symbol extraction.
2. Add an optional local conversation index filter by parsed symbol or status for review workflows.
3. Design an explicit safety gate for any future LLM/NLP integration before adding model calls.
4. Design a local-only alert delivery preview contract that consumes advisory artifacts without sending messages.
5. Keep paper workflow priority and advisory-only semantics covered before any delivery-channel or automation work.
