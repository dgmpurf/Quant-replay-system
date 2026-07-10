# Historical Replay Mixed STOCK/ETF Universe Profile Policy Post-v1.89 Governance Audit / Next Decision Planning Report-Only v0.1

## A. Decision / Status

phase = historical_replay_mixed_stock_etf_universe_profile_policy_post_v1_89_governance_audit_next_decision_planning
decision = ready
privacy_issue_stop = no
docs_only = yes
source_code_changed = no
tests_changed = no
runtime_changed = no
current_checkpoint = v1.89.0
current_checkpoint_commit = 7ca9c4d
current_checkpoint_tag = v1.89.0
previous_checkpoint = v1.88.0
previous_checkpoint_commit = 67af8d7
previous_checkpoint_tag = v1.88.0
external_project_source_version = v1.89.0_user_reported
mode_selection_calibration_overlay = applied_user_reported_2026_07_10
business_checkpoint_changed_by_mode_overlay = no
post_checkpoint_governance_audit_created = yes
selected_next_route = Historical Replay Mixed STOCK/ETF Universe Profile Policy Post-v1.89 Generated Artifact Review / Wording Audit Report-Only v0.1

Final classification:

`HISTORICAL_REPLAY_MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_POST_V1_89_GOVERNANCE_AUDIT_MODE_RECOMMENDATION_HARDENED_REPORT_ONLY`

Final verdict:

`HISTORICAL_REPLAY_MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_POST_V1_89_GOVERNANCE_AUDIT_READY_FOR_COMMIT_REPORT_ONLY`

The `v1.89.0` checkpoint is coherent and accepted as a report-only governance checkpoint. The safest next route is a bounded post-checkpoint generated artifact and live wording audit because the live recommendation still points to the tag/source readiness phase that has now completed.

## B. Current Git / Tag / External Source State

Preflight passed before this report was created:

- Branch: `main`.
- Worktree: clean.
- HEAD: `7ca9c4d` / full commit `7ca9c4dab80cd9e97bd84e0ebd093510ccc11d70`.
- `git describe --tags --always`: `v1.89.0`.
- Tag at HEAD: `v1.89.0`.
- Tag at `7ca9c4d`: `v1.89.0`.
- `v1.88.0`: remains at `67af8d7`.
- `v1.87.0`: remains at `85348df`.
- `git show --check 7ca9c4d`: clean.
- Initial `git diff --check`: clean.
- Repository `docs/project_sources` tree: absent.

External ChatGPT Project Source is recorded as user-reported at `v1.89.0`. The post-v1.89 mode-selection calibration overlay is also user-reported as applied on 2026-07-10. Neither external state is inferred from repository files, and no repository mirror is created.

The historical duplicate commits `9728367` and `b1ef749` remain untouched. The historical whitespace artifact on `9728367` is not amended, reset, rewritten, or retagged.

## C. v1.89 Checkpoint-Chain Audit

The accepted chain is coherent and linear:

1. `20fa33f` - post-v1.88 governance audit.
2. `6143583` - post-v1.88 artifact review.
3. `5998b9a` - no-hit post-v1.88 wording hardening.
4. `106450b` - mixed STOCK/ETF policy planning.
5. `530f268` - mixed profile policy fixture.
6. `4e741ab` - generated artifact review.
7. `92b91f9` - next-action wording hardening.
8. `cc44b2a` - `v1.89.0` checkpoint documentation.
9. `d5fb9b6` - checkpoint commit review.
10. `7e9aceb` - full non-slow pre-tag validation.
11. `2899bcd` - pre-tag readiness wording hardening.
12. `7ca9c4d` - tag/source readiness planning and final `v1.89.0` tag target.

The tag includes the final readiness report, matching the pre-tag rule. No missing governance step or tag-target mismatch was found.

## D. Validation-Evidence Audit

The committed validation record is complete for this report-only checkpoint:

| Evidence | Accepted result |
| --- | --- |
| Mixed profile fixture/views/CLI focused | 19 passed |
| Dashboard/research-status | 382 passed |
| Combined focused suite | 447 passed |
| Full non-slow | 6279 passed, 109 deselected, 5 warnings, 0 failures |
| Full non-slow runtime | 1587.73s (0:26:27) |
| Temp-root core/index/health/status/research-status | all exited 0 |
| Mixed policy health | `MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_HEALTH_PASS_REPORT_ONLY` |
| Research-status context | visible |

The five warnings are the previously recorded non-blocking pandas date-format inference and dtype future warnings. This audit does not rerun pytest, full non-slow, or CLI smoke.

## E. External Source Update Acknowledgement

The external Project Source update to `v1.89.0` is user-reported context only. This audit does not attempt to verify it from repository files, does not create an external package, and does not create Source update notes.

The repository remains the code and governance source of truth; the external Project Source is a curated review surface rather than a mirrored repository tree.

## F. Mode-Selection Calibration Acknowledgement

The post-v1.89 mode-selection calibration overlay is acknowledged as user-reported operating guidance applied on 2026-07-10. It changes task-routing guidance only. It does not change the `v1.89.0` business checkpoint, fixture data, counts, health semantics, research-status priority, or any approval boundary.

## G. Milestone Bundle Preference Acknowledgement

The milestone-bundle preference remains active. This task produces one consolidated docs-only governance audit and next-decision report. It is not split into several planning reports and is not expanded into artifact generation, wording implementation, evidence collection, or downstream execution.

## H. Selected Sample and Count Contract

selected_historical_decision_date = 2024-04-02
selected_universe = etf_core
selected_symbols = 000001, 000002, 159915, 300750, 510300, 600000, 600519, 601318, 688981
row_count = 9
stock_row_count = 7
etf_row_count = 2
profile_conflict_count = 7
profile_aligned_context_count = 2
unresolved_profile_conflict_count = 7
profile_policy_accepted_count = 0
universe_membership_approved_count = 0
official_status_evidence_accepted_count = 0
row_with_blocker_count = 9
safety_true_count = 0

The count contract is unchanged from planning through the tagged checkpoint. No selected row is accepted.

## I. STOCK/ETF Profile-Policy Interpretation

The seven STOCK rows remain unresolved profile conflicts under the legacy `etf_core` sample label:

`000001, 000002, 300750, 600000, 600519, 601318, 688981`

They retain STOCK-oriented profile context but have no approved universe membership, official status evidence, stock profile validation, PIT approval, replay authority, or financial authority.

The two ETF rows remain profile-aligned context only:

`159915, 510300`

Alignment means the instrument type and recommended profile agree with the legacy label. It is not official universe proof, status proof, survivorship proof, PIT approval, or downstream readiness.

## J. Research-Status and Workflow-Priority Audit

The mixed profile context remains visible in research-status. Focused dashboard evidence confirms that its report-only context does not override later workflow priority and preserves `PAPER_WORKFLOW_READY` when that higher-priority context is present.

The mode overlay does not alter this priority. The checkpoint remains diagnostic context and does not become an active workflow gate.

## K. Live Recommended-Next-Task Audit

The current live recommendation remains:

`Historical Replay Mixed STOCK/ETF Universe Profile Policy Tag and Source Readiness Planning Report-Only v0.1`

This wording was correct before the tag and is consistently present in core, CLI, dashboard, and positive focused test expectations. After `v1.89.0` was created and the external Source update was user-reported complete, it now points to a completed phase.

No source change is made by this audit. The stale post-tag route is the principal reason to select a bounded generated artifact review / wording audit as the next bridge. That next task should determine whether fresh temp-root artifact review is required and what post-v1.89 live next-action wording is safe.

## L. Safety and Non-Approval Boundary

profile_conflict_resolved = no
universe_membership_approved = no
stock_profile_validated = no
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

The tag and external Source acknowledgement do not grant any data, evidence, replay, model, buy-review, broker, or trading authority.

## M. Reviewer / Privacy / Source-Content Boundary

This audit reads tracked governance documents, Git metadata, live wording constants, and focused test expectations only. It does not inspect real source artifacts, source bytes, private paths, filled templates, reviewer identities, credentials, tokens, environment files, or authentication material.

Private reviewer identities and source content must not be bundled into a later report or external Source update. Reviewer references remain aliases or governance roles unless a separately approved privacy task establishes a different policy.

## N. Candidate Next Routes Reviewed

| Route | Decision | Reason |
| --- | --- | --- |
| A. Post-v1.89 Generated Artifact Review / Wording Audit Report-Only | selected | The live task still points to completed tag/source readiness, and no fresh post-tag artifact/wording review exists. |
| B. Official Manual Evidence Collection Fill Protocol Design Report-Only | not selected | Artifact and wording state should be audited before any fill-protocol design. |
| C. Source / Evidence Sufficiency Policy Planning Without Evidence Collection | not selected | No evidence-policy ambiguity was established by this repository audit. |
| D. Pause Repo Work and Collect Evidence Externally | not selected | The safe repository audit route remains available without evidence collection. |
| E. Continue Another Historical Replay Governance Feature | not selected | The mixed-profile branch still has a stale post-tag next-action surface. |
| F. Post-v1.89 Governance Hardening Report-Only | not selected | No ambiguity beyond the normal artifact/wording review was found. |

## O. Selected Next Route

Exactly one route is selected:

`Historical Replay Mixed STOCK/ETF Universe Profile Policy Post-v1.89 Generated Artifact Review / Wording Audit Report-Only v0.1`

## P. Why the Selected Route Is Safe

The selected route remains report-only and repository-centered. It can inspect the accepted fixture artifacts and live wording without collecting evidence, changing policy semantics, resolving conflicts, or advancing any downstream authority.

It is also the smallest bridge from a completed tag/source milestone to the next truthful live recommendation. It prevents a stale task string from being mistaken for unfinished tag work while keeping evidence collection and semantic expansion separately governed.

## Q. What Must Not Be Bundled

The next report must not bundle:

- source or test changes unless a later separately approved wording task explicitly allows them;
- generated repository outputs or protected data;
- Project Source packages or repository Source mirrors;
- Source update notes;
- private reviewer identities, source bytes, secrets, tokens, credentials, environment files, or auth material;
- official evidence collection, filled templates, accepted no-hit context, evidence acceptance, or closure;
- profile conflict resolution, universe membership approval, or stock profile validation;
- PIT approval, active replay input, replay execution, freeze, labels, metrics, training, models, weights, thresholds, paper expansion, buy-review, broker, API, LLM, order, message, or trading authority.

## R. Current-Task Mode Recommendation

Current task:

- primary surface: Codex
- environment: Local
- model: GPT-5.6 Terra
- effort: High
- speed: Standard
- primary acceptance artifact:
  - docs-only post-v1.89 governance audit report;
  - Git/tag/Source state proof;
  - static and protected-path scans;
  - exactly one selected safe route.
- reason: bounded repository-centered governance audit with mechanical acceptance evidence.
- escalation condition: escalate to Chat or Work with GPT-5.6 Sol, Extra High or Max effort, and Standard speed only if real evidence sufficiency, PIT adjudication, reviewer authority, identity/privacy authority, replay promotion, model governance, buy-review, or financial/trading authority must be decided.
- human approval gate: ChatGPT/user review is required before commit and before any next repository task.

`Pro Extended` is deprecated historical terminology in this mode-selection context and is not the active escalation label. Model strength or effort never grants additional authority.

## S. Next-Executable-Task Mode Recommendation

Next executable task:

- task: `Historical Replay Mixed STOCK/ETF Universe Profile Policy Post-v1.89 Generated Artifact Review / Wording Audit Report-Only v0.1`
- primary surface: Codex
- environment: Local
- model: GPT-5.6 Terra
- effort: High
- speed: Standard
- primary acceptance artifact:
  - docs-only post-checkpoint generated artifact and live-wording audit report;
  - fresh repo-external temp-root artifact evidence if later explicitly authorized;
  - Git scope proof;
  - safety scans;
  - exactly one next route.
- reason: the live `recommended_next_task` still points to the completed tag/source readiness phase, so a bounded post-checkpoint artifact and wording audit is the safest bridge.
- stop conditions:
  - source, test, or runtime modification is required;
  - evidence collection is required;
  - profile conflict resolution or universe membership adjudication is required;
  - PIT, replay, labels, metrics, model, stock profile, paper, buy-review, or trading boundaries would be crossed;
  - `docs/project_sources` or a Project Source package would be created.

If a stop condition requires high-risk semantic judgment, use Chat or Work with GPT-5.6 Sol, Extra High or Max effort, and Standard speed. That escalation changes review capability only; it does not grant additional authority.

## T. Commit / Tag / Source Recommendation

Recommended commit message if reviewed and ready:

`docs: audit historical replay mixed stock ETF universe profile policy post-v1.89 governance`

Recommended tag decision:

No tag for this post-v1.89 audit. Existing `v1.89.0` remains unchanged.

Recommended Source update decision:

No Source update for this post-v1.89 audit. External Project Source remains user-reported at `v1.89.0`.

### Verification Checks

- Static safety scan: no unsafe approval, readiness, or unresolved-marker match; the only match is the explicit negative repository Source-path statement.
- Protected tracked scan: only `data/processed/.gitkeep`, `data/raw/.gitkeep`, and `outputs/reports/.gitkeep`.
- Repository Source-path status: no output; direct existence check: false.
- `git diff --check`: clean.
- Final describe: `v1.89.0`.
- Tag at HEAD: `v1.89.0`.
- No test, full non-slow, or CLI command was run by this audit.

## U. Recommended Next Task

`Historical Replay Mixed STOCK/ETF Universe Profile Policy Post-v1.89 Generated Artifact Review / Wording Audit Report-Only v0.1`
