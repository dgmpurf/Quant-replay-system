# Personal MVP Phase Compression and Prompt Budget Planning v0.1

## A. Decision / Status

phase = personal_mvp_phase_compression_prompt_budget_planning  
decision = ready  
privacy_issue_stop = no  
docs_only = yes  
source_code_changed = no  
tests_changed = no  
runtime_changed = no  
selected_next_route = personal_mvp_advisory_surface_acceleration_planning_report_only

prompt_compression_means_reduce_codex_round_trips = yes  
prompt_compression_means_delete_safety_boundaries = no  
codex_prompts_default_english = yes  
chinese_allowed_only_for_literal_paths_or_names = yes  
user_facing_cmd_short_and_robust = yes  
adaptive_prompt_structure_required = yes  
single_fixed_prompt_template_required = no  
think_default_for_low_risk_review = yes  
pro_required_for_high_risk_semantics = yes  
pro_extended_required_for_source_synthesis = yes

source_hash_recompute_approved = no  
source_artifact_byte_read_deepening_approved = no  
available_time_pit_gate_approved = no  
real_package_candidate_creation_approved = no  
active_replay_input_approved = no  
replay_execution_approved = no  
labels_training_model_stock_profile_paper_approved = no  
buy_review_approved = no  
trading_approved = no  
data_raw_processed_cache_writes_approved = no

Final planning classification: `PERSONAL_MVP_PHASE_COMPRESSION_PROMPT_BUDGET_PLANNING_READY_REPORT_ONLY`.

Final planning verdict: `PERSONAL_MVP_PHASE_COMPRESSION_READY_FOR_ADVISORY_SURFACE_ACCELERATION_PLANNING`.

## B. Current Accepted State

The latest checkpoint tag is `v1.82.0` at commit `e247ab6`. The latest post-checkpoint governance audit is commit `7aa0cb6`, which selected `personal_mvp_phase_compression_and_prompt_budget_planning` as the next safe boundary.

The Source Artifact Byte-Hash boundary is complete for its narrow report-only v1.82.0 scope. It does not approve deeper Tiny PIT source/PIT/package semantics. The near-term project need is now delivery speed for the personal/family MVP path, while preserving institution-grade safety boundaries.

## C. Why Phase Compression Is Now Appropriate

The recent Tiny PIT sequence proved that the project can repeatedly implement core, artifact views, CLI, research-status, checkpoint, post-checkpoint audit, and next-decision planning while preserving strong report-only boundaries. That pattern is safe but expensive in Codex round trips.

Phase compression is appropriate because v1.82.0 did not leave an urgent unresolved blocker requiring more Tiny PIT deepening. The project can pause semantic expansion and use a planning pass to reduce redundant prompts around low-risk, structurally similar work.

## D. Definition of Prompt Compression

Prompt compression means reducing Codex round trips by bundling compatible low-risk tasks. It does not mean making every Codex prompt short. It does not mean removing hard boundaries, allowed files, forbidden files, STOP conditions, validation commands, disclosure checks, or final report requirements.

A compressed Codex prompt may still be long when the work needs explicit safety constraints. The compression target is the number of handoffs, not the clarity of the instructions.

## E. User-Facing CMD Rule

User-facing CMD blocks should be short, robust, and easy to copy.

Preferred CMD rules:

- Use `cd /d "<repo>"` as the first command when context matters.
- Put `git status --short --branch` before `git diff --check` in user-facing Git flows.
- Avoid multi-line caret continuations when a simpler one-line command is available.
- Prefer separate clear commands over clever chained commands for manual copy/paste flows.
- Keep protected tracked scans explicit and stable.
- Do not ask the user to run long validation when Codex can safely run it locally within the task boundary.

## F. Codex-Facing Prompt Language Rule

Codex-facing prompts should be English by default. English keeps file names, command syntax, status names, and safety boundaries less ambiguous for implementation and validation.

Chinese should remain only when it is part of a literal path, filename, repository name, project name, exact user-provided value, or user-facing explanation. User-facing summaries may remain Chinese when that is clearer for the user.

## G. Adaptive Prompt Structure Rule

Use adaptive prompt structure instead of one fixed mega-template.

Every prompt should still include:

- repo path and current accepted state;
- task type;
- explicit allowed files;
- explicit forbidden files/actions;
- STOP conditions;
- read-first evidence;
- validation commands;
- git safety checks;
- final response requirements.

Low-risk docs-only prompts can be shorter. Runtime implementation prompts need more detail. High-risk semantic prompts must include exact non-approvals and leakage boundaries.

## H. Bundlable Task Families

The following families can often be bundled when prior patterns are stable and the task explicitly allows it:

- Docs-only governance audit plus next-decision planning.
- Checkpoint docs plus validation evidence plus source-update recommendation.
- Artifact index, health, and status views for a stable report-only core.
- CLI command family plus focused CLI tests when the parser pattern already exists.
- Research-status integration plus local dashboard focused tests when fields are bounded and no priority changes are introduced.
- Wording hardening plus focused tests when semantics do not change.
- Source update package planning plus manifest generation when it is external/curated and excludes `src/`, `tests/`, `outputs/`, `data/`, secrets, and virtual environments.

Bundling requires clear rollback/STOP rules. If a bundled task discovers a semantic blocker, privacy issue, test failure requiring code redesign, or unexpected tracked generated data, Codex should stop and report instead of expanding scope.

## I. Non-Bundlable Safety Gates

Do not bundle tasks that introduce or alter any of these boundaries:

- source_hash recomputation beyond an already accepted narrow local metadata scope;
- deeper source artifact byte reading;
- source content reading;
- target CSV opening or parsing;
- expected_hash reverification;
- revision_id validation;
- available_time validation;
- available_time <= replay_decision_time PIT gate;
- PIT admissibility;
- source reliability scoring;
- reviewer authority validation;
- real package candidate creation;
- active reviewed input or active replay input;
- replay execution;
- replay decisions or replay freeze;
- forward labels or future-label joins;
- training/evaluation datasets, metrics, model training, weights, thresholds, probabilities, or predictions;
- stock_profile validation;
- paper validation or global approval changes;
- real buy-review eligibility or `buy_review_allowed`;
- broker/API/order/message/trading behavior;
- data/raw, data/processed, or data/cache writes;
- Project Source synthesis or major cross-document governance rewrites.

These need separate prompts and the appropriate ChatGPT mode.

## J. Mode Allocation Rule

ChatGPT Think should be the default for low-risk docs-only review, report-only planning, local wording checks, and straightforward governance summaries.

ChatGPT Pro is required when a response must judge high-risk semantics such as source_hash recomputation, source artifact byte-read deepening, available_time PIT gate, PIT admissibility, source reliability, reviewer authority, real package candidate, replay, labels, model, stock_profile, paper, buy-review, or trading.

ChatGPT Pro Extended is required for Project Source synthesis, cross-document Source updates, checkpoint-to-Source consolidation, source-pack curation, major roadmap/governance rewrites, or any task that must reconcile many documents into a durable external project anchor.

Codex medium is enough for simple docs-only edits, narrow wording fixes, and small local audits. Codex high should remain the default for implementation, checkpoint docs, artifact views, CLI integration, research-status integration, and pre-commit validation. Codex extra high should be reserved for subtle leakage, active-state boundary, privacy/source disclosure, paper/performance overclaim, or trading-safety issues.

## K. Testing Compression Rule

Testing can be tiered, not skipped.

Use focused tests first for narrow implementation. Use combined focused suites for bundled work touching multiple surfaces. Use `python -m pytest -m "not slow"` for broad pre-tag smoke when explicitly scoped. Use full `python -m pytest` before stable commits, checkpoints, or tags unless the prompt explicitly limits the task to docs-only planning and requests only Git/readability checks.

For docs-only planning like this task, do not run pytest unless the prompt requests it. Run `git status --short --branch`, `git describe --tags --always`, `git diff --check`, and any requested static scan.

## L. Checkpoint Compression Rule

Checkpoint docs can bundle:

- completed implementation chain;
- validation evidence;
- known limitations;
- safety boundaries;
- source update recommendation;
- recommended next task.

Checkpoint docs should not silently update runtime semantics, tests, or Project Source. Commit/tag remains a manual user step. If a checkpoint task discovers a validation blocker, it should stop before finalizing the checkpoint.

## M. Source Update Rule

Project Source remains curated and external. Do not recreate `docs/project_sources`. Do not mirror the repo into Git. Do not upload `src/`, `tests/`, `outputs/`, `data/`, manual diagnostics, secrets, or virtual environments as ChatGPT Project Source.

Use Pro Extended for cross-document Source synthesis. Changed-files-only Source updates should include curated markdown/source-context files and a manifest, not a repository diff mirror.

## N. Near-Term Personal MVP Acceleration Candidates

The strongest near-term candidates are usability and advisory-surface work, not deeper Tiny PIT source/PIT/package semantics.

Candidate 1: Personal MVP advisory surface gap planning.  
Map what the personal/family user can currently ask or inspect, what artifact lineage powers each answer, and what minimum local-only improvements would make the system easier to use without approving buy-review or trading.

Candidate 2: Single-symbol/question-style advisory consolidation planning.  
Review existing single-symbol, question-style answer, advisory conversation, signal advisory, and research-status docs to define one compact next implementation path for better user-facing review output.

Candidate 3: Local dashboard/readout usability planning.  
Improve how existing local research-status and advisory artifacts are summarized for repeated manual review, without changing signal semantics or active state.

Candidate 4: Prompt pack compression for recurring low-risk phases.  
Create a small set of reusable prompt outlines for docs-only audit, artifact views, research-status integration, checkpoint docs, and post-checkpoint next-decision tasks.

## O. Recommended Next Route

Selected route: `personal_mvp_advisory_surface_acceleration_planning_report_only`.

Rationale: the personal MVP needs fewer governance-only loops and more direct usability planning around existing advisory outputs. This route can improve the user path without approving real buy-review, performance validation, broker integration, orders, messages, or trading.

Pause further Tiny PIT deepening for now. Resume Tiny PIT source_hash, available_time, PIT gate, reviewer authority, or real package candidate work only after a separate Pro/Pro Extended review confirms that the personal MVP path needs it immediately.

## P. Explicit Non-Approvals

This planning document does not approve:

- source_hash recomputation;
- source artifact byte-read deepening;
- source content reading;
- target CSV opening;
- expected_hash reverification;
- revision_id validation;
- available_time validation;
- available_time PIT gate;
- PIT admissibility;
- source reliability scoring;
- reviewer authority validation;
- real package candidate creation;
- active reviewed input;
- active replay input;
- replay execution;
- labels/training/model/stock_profile/paper workflows;
- real buy-review eligibility;
- `buy_review_allowed`;
- strategy performance validation;
- broker/API/order/message/trading behavior;
- `data/raw`, `data/processed`, or `data/cache` writes.

## Q. Open Blockers

No blocker was found for adopting phase-compression planning as the next route.

## R. Non-Blocking Notes

- Prompt compression should be reviewed periodically. If bundled prompts become too broad to verify safely, split them again.
- Bundled phases should keep exact final-report requirements so ChatGPT review remains easy.
- Documentation-only tasks can use lighter validation, but implementation and checkpoint candidates still require the appropriate focused and broad test evidence.
- Personal MVP acceleration should preserve the current human-in-the-loop posture: local data, research artifacts, advisory signals, human confirmation, and reviewed paper workflow.

## S. Recommended Next Task

`Personal MVP Advisory Surface Acceleration Planning Report-Only v0.1`

The task should inspect product vision, existing advisory workflows, local dashboard/research-status summaries, single-symbol advisory, question-style answer, advisory conversation, signal advisory, paper workflow boundaries, and testing strategy. It should recommend the smallest safe implementation route that improves personal/family usability while preserving no real buy-review, no performance validation, no broker/order/message/API/trading, no active state mutation, and no protected data writes.
