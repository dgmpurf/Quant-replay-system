# Release Checkpoint v0.92.0: Shared Signal Semantics Provenance Visibility

## Milestone Name

Shared Signal Semantics Provenance Visibility v0.1.

Recommended tag: `v0.92.0`

## Completed Capabilities

- Downstream advisory artifacts record shared `signal_semantics` provenance fields.
- Advisory health checks validate provenance presence, policy source, and unsafe safety flags.
- Advisory index/status views expose provenance context for:
  - signal advisory
  - single-symbol advisory
  - question-style single-symbol answers
  - advisory conversation
- Unified `research-status` now exposes shared semantics provenance context.
- Legacy missing-provenance artifacts remain visible as `WARN` context instead of blocking later workflow state.
- Unsafe provenance remains actionable through health checks.
- Regenerated latest single-symbol advisory and question-style answer artifacts now carry provenance.
- Later paper workflow priority remains preserved.
- `REVIEW_BUY_CANDIDATE` remains human-review-only.
- `DEMO_ONLY` remains workflow validation only.
- No auto-order, broker integration, live trading, or real message sending was added.

## Workflow Impact

The advisory audit trail is now visible from source rows through product-facing advisory layers and dashboard status:

```text
current-candidates / scored rows
-> signal_semantics
-> shared semantics provenance
-> signal-advisory
-> single-symbol-advisory
-> question-style answer
-> advisory-conversation
-> artifact index / health / status
-> research-status
```

This milestone makes it easier to answer which local policy, classifier, version, and safety settings produced a visible advisory action. It does not approve trades, change execution behavior, or make non-demo labels strategy recommendations.

Typical provenance fields include:

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

## Latest Provenance Regeneration

Task 1 regenerated the latest local single-symbol advisory path from the 9-symbol demo candidates artifact:

```text
outputs/reports/current_candidates/2024-05-20_etf_core_f484cd4648/candidates.csv
```

Regenerated artifacts:

- latest single-symbol advisory run id: `e85df1e547c6`
- latest question-style answer run id: `d4eb0bbc450c`
- latest advisory-conversation run id: `e520cfafd370`
- symbol: `000001`
- parsed intent: `BUY_REVIEW`
- advisory action: `DEMO_ONLY`
- provenance source: `signal_semantics`
- provenance version: `v0.1`
- provenance classifier: `classify_signal_semantics_action`

Latest health/status outcomes:

- `single-symbol-advisory-health`: `WARN`, `82` warnings, `0` errors.
- `single-symbol-advisory-status`: latest `e85df1e547c6`, provenance present.
- `single-symbol-advisory-answer-health`: `WARN`, `39` warnings, `0` errors.
- `single-symbol-advisory-answer-status`: latest `d4eb0bbc450c`, provenance present.
- `advisory-conversation-health`: `WARN`, `3` warnings, `0` errors.
- `advisory-conversation-status`: latest `e520cfafd370`, provenance present.

The health warnings come from older local artifacts that remain indexed. The latest status views point at provenance-bearing artifacts.

Unified `research-status` after regeneration:

- status: `WARN`
- final workflow stage: `PAPER_WORKFLOW_READY`
- latest semantics action: `DEMO_ONLY`
- `semantics_provenance_present=True`
- `semantics_provenance_missing_legacy_count=0`
- later paper workflow priority preserved

## Validation Baseline

Latest known full validation before this documentation checkpoint:

- Backend tests: `1166 passed, 2 warnings`.
- Quick tests: `1057 passed, 109 deselected, 2 warnings`.

This checkpoint is documentation-only. The requested validation for this checkpoint is:

```cmd
python -m pytest -m "not slow"
```

## Safety Guarantees

- Provenance is audit metadata, not approval.
- `REVIEW_BUY_CANDIDATE` is not an order.
- `WATCH` is not an order.
- `DEMO_ONLY` is not a real strategy recommendation.
- No automatic BUY/SELL execution was implemented.
- No broker API was implemented.
- No live trading was implemented.
- No real SMS, email, Telegram, WeChat, or other message delivery was implemented.
- No LLM/API calls were implemented.
- Manual confirmation remains required.
- `auto_order_allowed=false` remains required.
- Generated outputs are ignored local artifacts and must not be committed.

## Known Limitations

- Legacy artifacts may still lack provenance and can continue to produce health warnings when full local history is scanned.
- Provenance does not validate strategy quality.
- Non-demo labels remain structural until calibrated and validated.
- Provenance visibility is observability, not trading approval.
- No real delivery channel is implemented.
- No automation is implemented.
- No international market support is implemented.

## Recommended Next Engineering Tasks

1. Review whether historical legacy artifacts should be archived, regenerated, or left as warning-only audit context.
2. Add a small provenance cleanup/status note if the local artifact directory becomes noisy from old warning-only artifacts.
3. Calibrate non-demo semantics only after strategy validation, data-quality gating, and backtesting evidence.
4. Keep delivery channels, automation, broker integration, and live trading out of scope until separately reviewed and checkpointed.
5. Create a release tag `v0.92.0` only after user review, git safety checks, and the normal checkpoint process.
