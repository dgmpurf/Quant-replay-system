# Release Checkpoint v0.91.0: Shared Signal Semantics Provenance Metadata

## Milestone Name

Shared Signal Semantics Provenance Metadata v0.1.

Recommended tag: `v0.91.0`

## Completed Capabilities

- Added the shared provenance helper `build_signal_semantics_provenance`.
- Added semantics provenance fields to signal advisory artifacts:
  - `signals.csv`
  - `metadata.json`
- Added semantics provenance fields to single-symbol advisory artifacts:
  - `single_symbol_advisory.csv`
  - `single_symbol_advisory.json`
  - `metadata.json`
- Added semantics provenance fields to question-style answer artifacts:
  - `single_symbol_advisory_answer.json`
  - `metadata.json`
- Added semantics provenance fields to advisory-conversation artifacts:
  - `advisory_conversation.json`
  - `metadata.json`
- Health checks now validate provenance presence and safety for:
  - signal advisory
  - single-symbol advisory
  - question-style answers
  - advisory conversation
- Legacy artifacts without provenance produce `MISSING_SEMANTICS_PROVENANCE` warnings.
- Unsafe provenance fails health, including unexpected policy source, semantics auto-order, live-trading provenance, or broker provenance.
- New dry-run artifacts include provenance and preserve local-only advisory safety.

## Workflow Impact

Downstream advisory artifacts now carry explicit evidence of the shared policy/classifier that produced the advisory action:

```text
current-candidates / scored rows
-> signal_semantics
-> shared provenance
-> signal-advisory
-> single-symbol-advisory
-> question-style answer
-> advisory-conversation
-> health checks / future dashboard visibility
```

The provenance fields make advisory output easier to audit before expanding dashboard visibility, alert preview workflows, or future delivery channels. They do not change advisory classification, execution state, or workflow priority.

Typical provenance fields include:

- `semantics_policy_source=signal_semantics`
- `semantics_policy_version=v0.1`
- `semantics_classifier=classify_signal_semantics_action`
- `semantics_settings_profile`
- `semantics_action`
- `semantics_reason`
- `semantics_manual_confirmation_required=true`
- `semantics_auto_order_allowed=false`
- `semantics_no_live_trading=true`
- `semantics_no_broker_api=true`

## Validation Baseline

- Backend tests: `1166 passed, 2 warnings`.
- Quick tests: `1057 passed, 109 deselected, 2 warnings`.

Latest local dry-run:

- Signal advisory:
  - signal_run_id: `2921a18906bf`
  - action count: `DEMO_ONLY=9`
  - provenance present
- Single-symbol advisory:
  - advisory_run_id: `45d8d039dd45`
  - symbol: `000001`
  - action: `DEMO_ONLY`
  - answer_run_id: `6f499e97ebe5`
  - provenance present
- Advisory conversation:
  - conversation_run_id: `e520cfafd370`
  - parsed_symbol: `000001`
  - parsed_intent: `BUY_REVIEW`
  - action: `DEMO_ONLY`
  - linked_answer_run_id: `75f5d1da7d96`
  - provenance present

Latest health results:

- `signal-advisory-health`: `PASS`, `0` issues.
- `single-symbol-advisory-health`: `WARN`, `2` legacy missing-provenance warnings, `0` errors.
- `single-symbol-advisory-answer-health`: `WARN`, `2` legacy missing-provenance warnings, `0` errors.
- `advisory-conversation-health`: `WARN`, `3` legacy missing-provenance warnings, `0` errors.

## Safety Guarantees

- Provenance is audit metadata, not approval.
- `REVIEW_BUY_CANDIDATE` remains human-review-only and is not an order.
- Demo rows remain `DEMO_ONLY`.
- No automatic BUY/SELL execution was implemented.
- No broker API was implemented.
- No live trading was implemented.
- No real message delivery was implemented.
- No LLM/API calls were implemented.
- Manual confirmation remains required.
- `auto_order_allowed=false` remains required.
- Generated outputs are ignored local artifacts and must not be committed.

## Known Limitations

- Older artifacts may lack provenance and will warn until regenerated.
- Index, status, and `research-status` summaries do not yet expose provenance fields directly.
- Provenance does not validate strategy quality.
- Non-demo labels remain structural until calibrated and validated.
- No real delivery channel is implemented.
- No automation is implemented.
- No broker integration or international market support is implemented.

## Recommended Next Engineering Tasks

1. Expose semantics provenance fields in advisory index/status summaries where useful.
2. Add unified `research-status` provenance visibility after the index/status fields are available.
3. Keep unsafe provenance failures blocking in health checks while preserving legacy artifact readability.
4. Calibrate non-demo semantics only after strategy validation, data-quality gating, and backtesting evidence.
5. Keep delivery channels, automation, broker integration, and live trading out of scope until separately reviewed and checkpointed.
6. Create a release tag `v0.91.0` only after user review, git safety checks, and the normal checkpoint process.
