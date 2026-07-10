# Historical Replay Mixed STOCK/ETF Universe Profile Policy Pre-Tag Readiness Wording Hardening Report-Only v0.1

## Decision

- decision: ready
- task_type: wording-only report-only hardening
- candidate_checkpoint_version: v1.89.0
- current_formal_checkpoint: v1.88.0 at 67af8d7
- source_of_truth_head: 7e9aceb
- tag_approved = no
- source_update_approved = no
- classification: HISTORICAL_REPLAY_MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_PRE_TAG_READINESS_WORDING_HARDENED_REPORT_ONLY
- verdict: HISTORICAL_REPLAY_MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_READY_FOR_TAG_AND_SOURCE_READINESS_PLANNING_REPORT_ONLY

This change hardens only the live `recommended_next_task` wording after the successful full non-slow pre-tag validation. It does not approve a tag, approve a Source update, change the mixed profile fixture contract, or grant any downstream authority.

## Preflight

- Branch was `main` with a clean worktree before changes.
- HEAD was `7e9aceb` and `git describe --tags --always` returned `v1.88.0-10-g7e9aceb`.
- No tag pointed at HEAD.
- `v1.88.0` pointed at `67af8d7`.
- `v1.89.0` did not exist.
- `git show --check 7e9aceb` and the initial `git diff --check` passed.
- The historical duplicate audit commits remain untouched; no history rewrite was attempted.

## RED-Equivalent Observation

Before the source change, the stale live route was present in:

- the core `RECOMMENDED_NEXT_TASK` constant;
- the mixed policy CLI next-task constant;
- the local research dashboard mixed-policy next-task constant;
- positive expectations in the core, views, CLI, and dashboard tests.

A read-only Python assertion required all three live constants to equal the new route and exited 1 with `AssertionError`. This established that the pre-change live surfaces had not yet advanced to tag and Source readiness planning.

## Wording Hardening

The live recommendation now reads:

`Historical Replay Mixed STOCK/ETF Universe Profile Policy Tag and Source Readiness Planning Report-Only v0.1`

The core, CLI, and dashboard constants were updated. Index and status surfaces continue to inherit the core constant, so no separate behavior or schema branch was added. Positive test expectations now require the new route, while the previous checkpoint-documentation route remains only in explicit `OLD_*` negative regression constants.

No artifact filename, row schema, symbol, sample date, universe, count contract, status vocabulary, blocker vocabulary, safety key, health rule, research-status priority rule, or evidence/PIT/replay/downstream authority behavior changed.

## Validation

| Validation | Result |
| --- | --- |
| Mixed profile core/views/CLI | 19 passed in 4.75s |
| Dashboard/research-status | 382 passed in 296.83s |
| Combined focused suite | 447 passed in 342.21s |
| Full non-slow | Not rerun; the clean 6279 passed, 109 deselected, 5 warnings result remains recorded at 7e9aceb |

## Temp-Root CLI Smoke

The final smoke root was outside the repository under `%TEMP%`:

`quant-replay-mixed-profile-wording-9b6a9a6930954aeaaf290a54ff35df71`

Core, index, health, status, and research-status commands all exited 0. All 21 generated files remained under the external temp root. The new route appeared in nine generated text artifacts, and the old route appeared in none.

- core runtime status: `MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_FIXTURE_CREATED_REPORT_ONLY`
- core health: `PASS`
- health view: `MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_HEALTH_PASS_REPORT_ONLY`
- research-status context visible: true
- isolated research-status: `WARN`, stage `DATA_PREPARATION_READY`
- isolated mixed-policy safety true count: 0

The isolated research-status stage reflects the intentionally minimal temp root. The focused dashboard test separately proved that an existing `PAPER_WORKFLOW_READY` stage remains the final priority when the mixed-policy context is present.

## Sample and Count Contract

- historical_decision_date: 2024-04-02
- universe: etf_core
- row_count: 9
- stock_row_count: 7
- etf_row_count: 2
- profile_conflict_count: 7
- profile_aligned_context_count: 2
- unresolved_profile_conflict_count: 7
- profile_policy_accepted_count: 0
- universe_membership_approved_count: 0
- official_status_evidence_accepted_count: 0
- row_with_blocker_count: 9
- safety_true_count: 0

## Safety and Non-Approval Boundary

The generated metadata retained:

- profile_conflict_resolved=false
- universe_membership_approved=false
- stock_profile_validated=false
- official_evidence_collection_started=false
- official_evidence_accepted=false
- official_evidence_closed=false
- pit_admissibility_approved=false
- active_replay_input=false
- replay_execution_allowed=false
- buy_review_allowed=false
- trading_allowed=false

No official evidence was collected, filled, accepted, or closed. No no-hit context was accepted. No profile conflict was resolved, no universe membership was approved, and no stock profile was validated. No replay input, replay execution, freeze, labels, metrics, training, model, paper expansion, buy-review, trading, broker, API, order, message, or LLM action was introduced. No protected data path was written.

## Scan and Git Safety

- Static safety scan result: pass; matches are limited to existing negative guards, parser/help surfaces, tests, and the negative `docs/project_sources` policy context.
- Old-route scan result: pass; the old live route remains only in four explicit negative regression constants.
- Protected tracked scan result: only `data/processed/.gitkeep`, `data/raw/.gitkeep`, and `outputs/reports/.gitkeep`.
- `docs/project_sources` status result: no output.
- Final `git diff --check`: pass.
- No tag points at HEAD and `v1.89.0` remains absent.

## Recommendation

Recommended next task:

`Historical Replay Mixed STOCK/ETF Universe Profile Policy Tag and Source Readiness Planning Report-Only v0.1`

Recommended commit message if reviewed and accepted:

`Harden historical replay mixed stock ETF universe profile policy pre-tag readiness wording`

No tag and no Source update are recommended for this wording-hardening task itself.
