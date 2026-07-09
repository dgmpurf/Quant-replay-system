# Historical Replay Mixed STOCK/ETF Universe Profile Policy Planning for legacy etf_core v0.1

## A. Decision / Status

```text
phase = historical_replay_mixed_stock_etf_universe_profile_policy_planning_legacy_etf_core
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
current_checkpoint = v1.88.0
current_checkpoint_commit = 67af8d7
current_checkpoint_tag = v1.88.0
current_repo_head = 5998b9a
external_project_source_version = v1.88.0_user_reported
mixed_stock_etf_profile_policy_planning_created = yes
profile_conflict_resolved = no
universe_membership_approved = no
stock_profile_validated = no
selected_next_route = Historical Replay Mixed STOCK/ETF Universe Profile Policy Contract / Fixture Report-Only v0.1
```

```text
official_source_hierarchy_approved = no
official_evidence_collection_started = no
official_evidence_collection_approved = no
official_evidence_accepted = no
official_evidence_closed = no
official_status_evidence_closure_approved = no
pit_evidence_closure_approved = no
pit_admissibility_approved = no
active_replay_input_approved = no
real_replay_execution_approved = no
replay_decision_freeze_approved = no
forward_labels_created = no
forward_label_creation_approved = no
training_dataset_created = no
metric_computation_approved = no
model_training_approved = no
weights_or_thresholds_adjustment_approved = no
stock_profile_expansion_approved = no
paper_expansion_approved = no
real_buy_review_approved = no
buy_review_allowed = no
trading_allowed = no
broker_api_approved = no
order_placement_approved = no
message_delivery_approved = no
external_api_or_llm_approved = no
current_candidates_execution_approved = no
snapshot_build_approved = no
signal_semantics_mutation_approved = no
data_raw_processed_cache_writes_approved = no
docs_project_sources_created = no
```

Final classification:

```text
HISTORICAL_REPLAY_MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_PLANNING_CREATED_REPORT_ONLY
```

Final verdict:

```text
HISTORICAL_REPLAY_MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_PLANNING_READY_FOR_CONTRACT_FIXTURE_REPORT_ONLY
```

## B. Current Git / tag / Source state

Preflight confirmed the expected current state before this report was created:

| Check | Result |
| --- | --- |
| Branch/status | `## main...origin/main` |
| HEAD | `5998b9a Harden historical replay reviewer no-hit acceptance fixture post-v1.88 next action wording` |
| `git describe --tags --always` | `v1.88.0-3-g5998b9a` |
| Tag at HEAD | no output |
| Tag at `67af8d7` | `v1.88.0` |
| Tag at `85348df` | `v1.87.0` |
| Tag at `69f98eb` | `v1.86.0` |
| `git tag --list v1.88.0` | `v1.88.0` |
| `git tag --list v1.87.0` | `v1.87.0` |
| `git show --check 5998b9a` | exit 0 |
| `git diff --check` before report | exit 0 |

External ChatGPT Project Source is user-reported as updated to `v1.88.0`. This planning report does not create a Project Source package, Source update note, checkpoint tag, or repo-side Project Source tree.

Known historical context is preserved: duplicate post-v1.87 governance audit commits remain in history, the known historical whitespace artifact on `9728367` is not rewritten, and no amend, reset, retag, or history rewrite is part of this task.

## C. Selected sample and mixed profile context

Selected sample:

```text
historical_decision_date = 2024-04-02
universe = etf_core
```

Selected symbols:

```text
000001, 000002, 159915, 300750, 510300, 600000, 600519, 601318, 688981
```

Current count contract:

| Field | Value |
| --- | ---: |
| row_count | 9 |
| stock_row_count | 7 |
| etf_row_count | 2 |
| profile_conflict_count | 7 |
| no_hit_row_count | 9 |
| not_accepted_count | 9 |
| accepted_context_count | 0 |
| row_with_blocker_count | 9 |
| survivorship_warning_count | 9 |
| safety_true_count | 0 |

Current selected sample profile shape:

| selected_symbol | instrument_type | legacy_universe_label | recommended_profile | profile_conflict |
| --- | --- | --- | --- | --- |
| 000001 | STOCK | etf_core | stock_core | true |
| 000002 | STOCK | etf_core | stock_core | true |
| 159915 | ETF | etf_core | etf_core | false |
| 300750 | STOCK | etf_core | stock_core | true |
| 510300 | ETF | etf_core | etf_core | false |
| 600000 | STOCK | etf_core | stock_core | true |
| 600519 | STOCK | etf_core | stock_core | true |
| 601318 | STOCK | etf_core | stock_core | true |
| 688981 | STOCK | etf_core | stock_core | true |

This planning report treats the mixed STOCK/ETF shape as unresolved policy context. It does not resolve the seven STOCK profile conflicts and does not convert the two ETF aligned rows into universe membership proof.

## D. What legacy `etf_core` means

`legacy_universe_label = etf_core` means historical sample context only. It records how the selected sample was labeled in the existing historical replay audit chain.

It does not prove:

- that each symbol belonged to an ETF-only universe on `2024-04-02`;
- that any STOCK row was intentionally eligible for an ETF core universe;
- that any ETF row had official universe membership evidence;
- that the sample is point-in-time admissible;
- that same-day quotation presence proves official status;
- that survivorship, listing, delisting, ST/no-ST, suspension, trading status, or ETF not-applicable policy evidence is complete.

The label must remain visible because it is part of lineage. It must not be used as a shortcut for official status or universe membership approval.

## E. What recommended profile means

`recommended_profile` is a policy hint derived from instrument type context, not an active profile decision.

`recommended_profile = stock_core` means the row should follow a STOCK-specific future profile policy path. It is not stock_profile validation, not evidence closure, not universe approval, and not buy-review eligibility.

`recommended_profile = etf_core` means the row should follow an ETF-specific future profile policy path. It is not universe proof, not official ETF status proof, not survivorship proof, and not point-in-time approval.

Recommended profile values may help route a later report-only contract fixture into the correct evidence family, but they must not be interpreted as active stock_profile, active replay input, replay readiness, paper expansion, buy-review permission, or trading permission.

## F. STOCK row policy

The seven STOCK rows under legacy `etf_core` remain unresolved profile-policy conflicts:

```text
000001, 000002, 300750, 600000, 600519, 601318, 688981
```

Required STOCK policy:

- Preserve `legacy_universe_label = etf_core` as lineage context.
- Preserve `recommended_profile = stock_core` as a routing hint only.
- Preserve `profile_conflict = true` until a later report-only contract explicitly adjudicates profile policy.
- Require STOCK-specific official-status evidence before any future evidence closure can be considered.
- Require STOCK ST/no-ST evidence or a documented STOCK status policy.
- Require universe membership evidence rather than relying on the legacy universe label.
- Keep survivorship warnings visible.
- Keep no-hit context separate from official status evidence.

STOCK row policy must not validate stock_profile, resolve universe membership, approve point-in-time admissibility, create replay readiness, approve buy-review, or authorize trading.

## G. ETF row policy

The two ETF rows align with the legacy label at the profile-hint level:

```text
159915, 510300
```

For these rows, `profile_conflict = false` means only that `instrument_type = ETF` and `recommended_profile = etf_core` align with the legacy `etf_core` label. It does not prove official universe membership, official ETF status, survivorship, trading status, suspension status, or point-in-time admissibility.

Required ETF policy:

- Preserve `recommended_profile = etf_core` as context only.
- Require ETF-specific official-status or source-policy evidence before any future closure.
- Keep ETF ST not-applicable policy separate from STOCK ST/no-ST evidence.
- Do not import STOCK ST/no-ST assumptions into ETF rows.
- Do not treat same-day quotation presence as official ETF status proof.
- Do not use no-hit context to fill missing ETF evidence.

ETF row policy must not approve replay readiness, buy-review readiness, paper expansion, performance validation, or trading.

## H. Universe membership and official status boundary

Universe membership requires explicit evidence in a later approved workflow. The current planning task does not collect that evidence and does not decide membership.

Official status evidence remains separate from profile policy. A future workflow must keep these evidence families distinct:

| Evidence family | Required boundary |
| --- | --- |
| Instrument type | Must distinguish STOCK and ETF rows without using the legacy label as proof. |
| Universe membership | Must require explicit evidence or documented policy, not only `legacy_universe_label`. |
| STOCK official status | Must include STOCK-specific listed/active, ST/no-ST, delisting, suspension, and trading-status policy where relevant. |
| ETF official status | Must include ETF-specific official-status and ETF ST not-applicable policy. |
| Survivorship | Must remain warning-visible until separately reviewed. |
| Same-day quotation | May be context only; it is not official status proof. |
| Forward return | Future information; it must not enter decision-time policy or evidence closure. |

The 8-layer factor taxonomy remains the primary structure for future research expansion. Fixed 12 factors are not final and must not become a hidden constraint on profile policy.

## I. No-hit interaction boundary

No-hit context remains a reviewer handoff surface only.

No-hit context cannot:

- resolve profile conflicts;
- prove universe membership;
- replace official status evidence;
- prove source reliability;
- approve point-in-time admissibility;
- override missing reviewer scope;
- override missing source lineage;
- close survivorship warnings;
- turn same-day quotation context into official evidence;
- create replay readiness, buy-review readiness, or trading permission.

Every current no-hit row remains `not_accepted`, with `accepted_context_count = 0`. Future mixed profile policy must keep no-hit status separate from profile-policy status.

## J. Required future profile policy fields

A later report-only contract/fixture should define these fields:

| Field | Meaning | Current planning use | Forbidden interpretation |
| --- | --- | --- | --- |
| selected_symbol | Selected sample symbol | Required lineage | Not universe proof |
| instrument_type | STOCK or ETF classification context | Required routing input | Not official status proof |
| legacy_universe_label | Historical sample label | Required lineage | Not membership proof |
| recommended_profile | Suggested profile family | Policy hint only | Not stock_profile validation |
| profile_conflict | Whether profile hint conflicts with legacy label | Must remain visible | Not a resolved blocker |
| profile_policy_status | Future controlled status | Not set to an accepted status here | Not PIT approval |
| universe_membership_evidence_required | Whether membership evidence is required | Always yes for this sample | Not evidence collected |
| official_status_evidence_required | Whether official status evidence is required | Always yes | Not evidence accepted |
| st_policy_family_required | STOCK ST/no-ST policy need | STOCK rows require it | Not ETF policy |
| etf_not_applicable_policy_required | ETF-specific ST not-applicable policy need | ETF rows require it | Not STOCK status evidence |
| profile_policy_reviewer_required | Reviewer accountability need | Future yes | Not approval by itself |
| profile_policy_reviewer_alias | Non-private reviewer alias | Future required | Not private identity |
| profile_policy_reviewer_scope | Reviewer scope | Future required | Not override authority |
| profile_policy_rationale | Human-readable rationale | Future required | Not evidence closure |
| profile_policy_limitation_note | Limitation note | Future required | Not hidden caveat |
| profile_policy_downstream_use_policy | Allowed downstream use | Context only | Not replay readiness |
| profile_policy_no_hit_override_allowed | Whether no-hit may override profile policy | Must be no | Not no-hit acceptance |
| profile_policy_pit_approval_allowed | Whether profile policy may approve PIT | Must be no | Not PIT approval |
| profile_policy_replay_readiness_allowed | Whether replay readiness may be emitted | Must be no | Not active replay input |
| profile_policy_buy_review_allowed | Whether buy-review may be allowed | Must be no | Not real buy-review |
| profile_policy_trading_allowed | Whether trading may be allowed | Must be no | Not trading permission |

## K. Profile policy status vocabulary

Future status vocabulary should be conservative:

| Status | Meaning | Current planning use |
| --- | --- | --- |
| unresolved_profile_conflict | Profile policy is unresolved and visible | Appropriate for STOCK conflicts in a future fixture |
| profile_aligned_context_only_not_universe_proof | Profile hint aligns with legacy label but does not prove membership | Appropriate for ETF rows in a future fixture |
| stock_profile_policy_required | STOCK row needs a STOCK-specific policy path | Future planning context only |
| etf_profile_policy_required | ETF row needs an ETF-specific policy path | Future planning context only |
| rejected_by_missing_instrument_type_evidence | Instrument type evidence is missing | Future blocker |
| rejected_by_missing_universe_membership_evidence | Universe membership evidence is missing | Future blocker |
| rejected_by_missing_official_status_evidence | Official status evidence is missing | Future blocker |
| rejected_by_legacy_label_only | Legacy label is the only support offered | Future blocker |
| accepted_for_policy_context_only_not_pit_approved | Future context-only policy acceptance, not PIT approval | Listed for design completeness only; not set by this planning task |

This planning report does not set any accepted profile-policy status. A future contract may include the final status only if it remains context-only, report-only, and explicitly non-approval.

## L. Profile policy blocker vocabulary

Required future blockers:

| Blocker | Meaning |
| --- | --- |
| blocker_legacy_universe_label_used_as_universe_proof | Legacy label was treated as membership evidence. |
| blocker_recommended_profile_used_as_stock_profile_validation | Recommended profile was treated as stock_profile validation. |
| blocker_profile_conflict_hidden_or_removed | Profile conflict was hidden, removed, or silently resolved. |
| blocker_missing_instrument_type_evidence | Instrument type evidence is missing. |
| blocker_missing_universe_membership_evidence | Universe membership evidence is missing. |
| blocker_missing_official_status_evidence | Official status evidence is missing. |
| blocker_missing_stock_st_no_st_evidence | STOCK ST/no-ST evidence or policy is missing. |
| blocker_missing_etf_st_not_applicable_policy | ETF ST not-applicable policy is missing. |
| blocker_no_hit_used_to_resolve_profile_conflict | No-hit context was used to resolve profile conflict. |
| blocker_no_hit_used_as_universe_proof | No-hit context was used as universe membership proof. |
| blocker_no_hit_used_as_official_evidence | No-hit context was used as official evidence. |
| blocker_same_day_quote_used_as_status_proof | Same-day quote was used as official status proof. |
| blocker_forward_return_used_in_decision_context | Future return entered decision-time context. |
| blocker_profile_policy_used_as_pit_approval | Profile policy was treated as PIT approval. |
| blocker_profile_policy_used_as_replay_readiness | Profile policy was treated as replay readiness. |
| blocker_profile_policy_used_as_buy_review | Profile policy was treated as buy-review permission. |
| blocker_profile_policy_used_as_trading_permission | Profile policy was treated as trading permission. |
| blocker_missing_profile_policy_reviewer_scope | Reviewer scope is missing. |
| blocker_private_reviewer_identity_disclosed | Private reviewer identity was disclosed. |
| blocker_forbidden_downstream_flag | Any forbidden downstream flag is true. |

## M. Future validation rules

A future report-only contract/fixture should validate:

1. The selected sample has exactly nine rows.
2. The selected symbols match the v1.88 no-hit fixture lineage.
3. Seven STOCK rows remain `profile_conflict = true` unless a later approved policy explicitly changes that status.
4. Two ETF rows remain `profile_conflict = false` only as profile-aligned context.
5. Every row keeps `legacy_universe_label = etf_core` visible.
6. No row uses `legacy_universe_label` as universe proof.
7. No row uses `recommended_profile` as stock_profile validation.
8. No row uses no-hit context to resolve profile conflict.
9. No row uses same-day quotation as official status proof.
10. No row uses forward returns in decision-time context.
11. STOCK rows require STOCK-specific official-status and ST/no-ST policy.
12. ETF rows require ETF-specific official-status and ETF not-applicable policy.
13. Reviewer alias and scope are required for future non-default policy status.
14. Private reviewer identity disclosure blocks.
15. Every downstream approval flag remains false.
16. Output remains docs/report-only or manual-diagnostics only in later implementation, never protected data paths.

## N. Future focused test plan

For `Historical Replay Mixed STOCK/ETF Universe Profile Policy Contract / Fixture Report-Only v0.1`, focused tests should cover:

| Test area | Expected assertion |
| --- | --- |
| selected rows | The nine expected symbols are present and ordered or deterministically sorted. |
| count contract | row count 9, STOCK 7, ETF 2, profile conflicts 7. |
| STOCK policy | STOCK rows require stock_core policy and preserve conflict visibility. |
| ETF policy | ETF rows align as context only and do not prove universe membership. |
| legacy label boundary | `legacy_universe_label` cannot satisfy membership evidence. |
| recommended profile boundary | `recommended_profile` cannot satisfy stock_profile validation. |
| no-hit boundary | no-hit cannot resolve conflicts or replace official evidence. |
| same-day quote boundary | same-day quote cannot satisfy official status proof. |
| forward-return boundary | future returns are forbidden in decision context. |
| reviewer policy | reviewer alias/scope required for future review context. |
| safety flags | buy-review, trading, replay, labels, model, stock_profile, current-candidates, snapshot, and protected data flags remain false. |
| report text | output states report-only and non-approval boundaries. |

Suggested future focused test files:

```text
tests/test_historical_replay_mixed_stock_etf_universe_profile_policy.py
tests/test_historical_replay_mixed_stock_etf_universe_profile_policy_views.py
tests/test_historical_replay_mixed_stock_etf_universe_profile_policy_cli.py
tests/test_local_research_dashboard.py
```

## O. Future temp-root smoke plan

If a later report-only fixture is implemented, temp-root smoke should use a repo-external temp directory and run only the new command family:

```text
historical-replay-mixed-stock-etf-universe-profile-policy
historical-replay-mixed-stock-etf-universe-profile-policy-index
historical-replay-mixed-stock-etf-universe-profile-policy-health
historical-replay-mixed-stock-etf-universe-profile-policy-status
research-status
```

Smoke should assert:

- generated artifacts remain under the temp root;
- no protected data paths are written;
- no Project Source files are created;
- row count and profile conflict counts match the current contract;
- no accepted profile-policy status is emitted by default;
- no evidence collection, evidence closure, PIT approval, replay readiness, buy-review, or trading flag is true;
- research-status exposes context without overriding later paper workflow priority.

## P. Safety and non-approval boundary

This planning report is docs-only. It does not:

- resolve profile conflicts;
- prove universe membership;
- validate stock_profile;
- collect official evidence;
- fill evidence templates;
- accept no-hit context as evidence;
- accept official evidence;
- close official evidence;
- approve PIT admissibility;
- create active replay input;
- run replay;
- freeze replay decisions;
- create forward labels;
- compute metrics;
- create training/evaluation datasets;
- train models;
- adjust weights, thresholds, formulas, or model parameters;
- expand paper authority;
- execute current-candidates;
- build snapshots;
- mutate signal semantics;
- approve buy-review;
- authorize broker/API/order/message behavior;
- call external APIs or LLM APIs;
- authorize trading;
- write protected data paths.

## Q. Candidate next routes reviewed

| Route | Decision | Reason |
| --- | --- | --- |
| A. Historical Replay Mixed STOCK/ETF Universe Profile Policy Contract / Fixture Report-Only v0.1 | selected | Planning is coherent and a bounded report-only contract/fixture is safe next. |
| B. Historical Replay Mixed STOCK/ETF Universe Profile Policy Planning Hardening Report-Only v0.1 | not selected | No missing field/status/blocker definitions were found that require a separate planning hardening pass. |
| C. Historical Replay Official Manual Evidence Collection Fill Protocol Design Report-Only v0.1 | not selected | Stabilizing mixed profile policy first is safer before any fill protocol design. |
| D. Pause repo work and manually collect official source/status evidence outside the repo | not selected | Repo work can continue in report-only policy-contract form without collecting evidence. |
| E. Historical Replay Reviewer No-Hit Acceptance Fixture Additional Hardening Report-Only v0.1 | not selected | The post-v1.88 wording hardening already routed live next action correctly. |
| F. Continue next historical replay governance feature outside mixed profile policy | not selected | The mixed profile blocker is the direct next safe governance surface. |

## R. Selected next route

Selected next route:

```text
Historical Replay Mixed STOCK/ETF Universe Profile Policy Contract / Fixture Report-Only v0.1
```

## S. Why selected route is safe

The selected route is safe because it can convert this planning vocabulary into a deterministic report-only contract surface without collecting evidence, resolving conflicts, approving PIT, creating replay input, or changing downstream authority.

It addresses the dominant policy blocker in the selected sample: seven STOCK rows are visible under a legacy ETF-labeled sample and need a policy contract before any evidence fill, official status closure, replay input, or buy-review workflow is considered.

## T. What must not be bundled

The next route must not bundle:

- official evidence collection or fetching;
- website reads, API reads, or source artifact reads;
- filled evidence templates;
- no-hit acceptance as evidence;
- official evidence acceptance or closure;
- PIT approval;
- active replay input or replay execution;
- replay decision freeze;
- forward label creation;
- metric computation outside focused tests;
- training, model, stock_profile, or paper expansion;
- weight, threshold, formula, factor, or model adjustment;
- buy-review or trading;
- broker/API/order/message/LLM calls;
- current-candidates execution;
- snapshot build;
- signal semantics mutation;
- protected data writes;
- Project Source package creation;
- checkpoint tag creation.

## U. ChatGPT/Codex mode recommendation

Recommended next mode:

```text
Codex high
```

Rationale: the next task is a narrow implementation-ready report-only contract/fixture. It should use deterministic local data already present in the fixture lineage and should not require Pro Extended unless the task introduces real official evidence semantics, human identity policy beyond aliases, source reliability scoring, actual universe membership adjudication, PIT admissibility decisions, or downstream workflow authority.

Use ChatGPT Pro / Pro Extended before implementation only if the next prompt attempts to:

- adjudicate real universe membership;
- define official evidence sufficiency;
- change ST/no-ST or ETF not-applicable policy in a way that affects eligibility;
- introduce source reliability scoring;
- interpret no-hit context as evidence;
- approve PIT admissibility;
- connect policy status to replay readiness, buy-review, paper expansion, or trading.

## V. Commit/tag/Source recommendation

Recommended commit message if ready:

```text
docs: plan historical replay mixed stock ETF universe profile policy
```

Recommended tag:

```text
No tag for this planning report.
```

Recommended Source update:

```text
No Source update for this planning report.
```

This report is a small docs-only planning handoff after v1.88.0. Source update should wait for a larger accepted checkpoint or an explicitly requested Source package task.

## W. Recommended next task

Recommended next task:

```text
Historical Replay Mixed STOCK/ETF Universe Profile Policy Contract / Fixture Report-Only v0.1
```

Implementation outline for that next task:

1. Create a deterministic report-only core fixture using the nine selected symbols and the policy fields defined here.
2. Keep every downstream approval flag false.
3. Preserve seven STOCK profile conflicts and two ETF profile-aligned context rows.
4. Write only report-only manual diagnostics artifacts or tmp-path artifacts in tests.
5. Add focused tests for counts, status vocabulary, blocker vocabulary, no-hit separation, official evidence separation, and safety flags.
6. Add views/CLI/research-status only in later separate tasks, not bundled into the core contract task unless explicitly scoped.
7. Do not collect official evidence, fill evidence templates, approve PIT, create active replay input, run replay, create labels, compute metrics, train models, validate stock_profile, expand paper authority, approve buy-review, or authorize trading.
