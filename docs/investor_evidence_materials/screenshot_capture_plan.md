# Screenshot Capture Plan

## Capture rules

Use a 16:9 canvas, repository-relative labels, a clean Markdown preview or code-editor view, and a font size readable from a presentation screen. Capture only the section needed to prove the point.

Hide or crop:

- drive letters, operating-system user names, and absolute local paths;
- `.env`, credentials, tokens, secret assignments, and terminal history;
- raw vendor/source payloads, private reviewer identity, and private limitation text;
- full hashes, machine-specific artifact identifiers, and irrelevant commit details;
- stale or demo states unless the slide explicitly explains them;
- any table or label that could be mistaken for a live recommendation, executed return, broker action, or production status.

## A. Repository proof

| ID | Source and capture surface | Purpose | Recommended crop | Information that must be hidden | Investor message |
| --- | --- | --- | --- | --- | --- |
| R1 | [README.md](../../README.md) in Markdown preview | Prove the documented breadth and the explicit included/not-included boundary | Crop the `MVP v0.1` heading, representative included capabilities, and the complete `Not included` list | Local editor title bars with absolute paths; unrelated historical sections | “This is an organized research platform foundation, and it explicitly excludes live broker trading, production strategy claims, and auto-order placement.” |
| R2 | Code editor file explorer at repository root | Prove repository structure | Show `config/`, `docs/`, `src/`, and `tests/`; keep `data/` and `outputs/` collapsed | `.env`, raw files, generated artifact names, user/machine paths, Git decorations that distract from structure | “Data, documentation, implementation, and validation are separated into auditable areas.” |
| R3 | `docs/` file explorer filtered to core topics | Prove documentation organization | Show a curated set: `data_contract.md`, `replay_run_orchestrator.md`, `factor_definition_schema_fixture.md`, `signal_advisory.md`, `testing_strategy.md`, and `local_research_workflow_e2e.md` | Hundreds of unrelated checkpoint files; anything making the frame unreadable | “The project documents its core contracts and safety boundaries as first-class engineering assets.” |

## B. Architecture proof

| ID | Source and capture surface | Purpose | Recommended crop | Information that must be hidden | Investor message |
| --- | --- | --- | --- | --- | --- |
| A1 | [architecture_for_investor.md](../investor_materials/architecture_for_investor.md) rendered in Markdown | Show the investor-friendly system architecture | Capture the five-layer Mermaid diagram and the boundary sentence directly below it | Editor chrome, absolute paths, unrelated source links | “Governed data flows through research and replay into advisory and human review; governance crosses every layer.” |
| A2 | [local_research_workflow_e2e.md](../local_research_workflow_e2e.md) | Show the operational workflow | Crop the list of workflow components and the CLI-style sequence from data preparation through `research-status` | Temporary paths, command prompt/user path, any fixture detail not needed for the flow | “The architecture is connected by explicit artifacts and handoffs, not by a single opaque model call.” |

## C. Research proof

| ID | Source and capture surface | Purpose | Recommended crop | Information that must be hidden | Investor message |
| --- | --- | --- | --- | --- | --- |
| Q1 | [factor_definition_schema_fixture.md](../factor_definition_schema_fixture.md), `Taxonomy Policy` | Prove the primary factor framework | Fit all eight canonical layers plus the fixed-12 disclaimer in one frame | Commands and output paths; any suggestion that fixture rows are active signals | “The factor ontology is broad and expandable; the fixed 12-factor list is only a checklist, not the final model.” |
| Q2 | [replay_run_orchestrator.md](../replay_run_orchestrator.md), `Purpose` and `Full Replay Flow` | Explain Historical Replay | Show the research question and the eight numbered steps | Function signatures, local paths, or simulated result values | “Historical Replay reconstructs what the system could have known and selected, then measures a later simulated outcome for research validation.” |
| Q3 | [data_contract.md](../data_contract.md), `Timestamp Fields` and `Core Eligibility Rule` | Prove the PIT concept | Keep the timestamp definitions and `available_time <= decision_time` in the same crop | Example machine paths, source identifiers, or unrelated schemas | “A row is usable only if it was available at the decision time, which guards against hindsight leakage.” |
| Q4 | [walk_forward_validation.md](../walk_forward_validation.md), `Why Walk-Forward Validation Matters` | Show research discipline beyond one backtest | Crop the train/validation/test explanation and the statement that the goal is not to prove future performance | Parameter values or sample returns that could be interpreted as investment claims | “The research workflow separates parameter selection from later evaluation to make overfitting visible.” |

## D. Engineering proof

| ID | Source and capture surface | Purpose | Recommended crop | Information that must be hidden | Investor message |
| --- | --- | --- | --- | --- | --- |
| E1 | [testing_strategy.md](../testing_strategy.md), `Test Markers` and `Recommended Commands` | Show the validation philosophy | Capture unit, integration, E2E, and slow tiers plus the local-only statement | Virtual-environment path, machine information, unrelated command history | “Validation covers narrow calculations, multi-module behavior, end-to-end wiring, and artifact-heavy workflows.” |
| E2 | [accepted_lineage_registry_windows_stable_directory_identity_correction_v0_1.md](../accepted_lineage_registry_windows_stable_directory_identity_correction_v0_1.md), `Validation` | Show a dated large regression result | Crop the document title and validation bullets containing focused, platform, and `6705 passed` results | Commit hashes, local temp paths, unrelated implementation detail | “The repository records full-suite and platform-specific gates at named checkpoints.” |
| E3 | [local_research_workflow_e2e.md](../local_research_workflow_e2e.md), `Automated Test` and `No-Live-Trading Guarantee` | Show that engineering proof includes negative safety assertions | Capture the verified workflow outputs and no-broker/no-network bullets | Temporary fixture names beyond what is necessary | “Tests verify both that artifacts are produced and that prohibited broker/network paths are not invoked.” |
| E4 | [local_research_dashboard.md](../local_research_dashboard.md), `Purpose` and `Relationship To Other Dashboards` | Show status-report design | Crop the questions the dashboard answers and the relationship among data-prep, paper-workflow, and `research-status` views | Long output-root lists and machine paths | “The system exposes health, blockers, and next manual actions instead of hiding incomplete state.” |

At package-preparation time, the most recently inspected generated local dashboard was `NO_DATA` and too wide for an investor slide. Do not capture it as product proof. A later, separately authorized sanitized demo run should be checked for freshness, width, and disclosure safety before use. Likewise, a checkpoint test screenshot is dated evidence; rerun tests separately if a deck needs a current-HEAD claim.

## E. Product proof

| ID | Source and capture surface | Purpose | Recommended crop | Information that must be hidden | Investor message |
| --- | --- | --- | --- | --- | --- |
| P1 | [signal_advisory.md](../signal_advisory.md), `Purpose` and `Contract` | Show how research becomes a review artifact | Capture the candidate-to-advisory-to-human-review flow and fields for reasons, validity, invalidation, risk, and manual confirmation | CLI paths, output IDs, source candidate paths, or any row that looks like a current recommendation | “The advisory layer explains what to review and why, while preserving manual confirmation and disabling auto-order.” |
| P2 | [personal_mvp_daily_advisory_review.md](../personal_mvp_daily_advisory_review.md), `Artifact Roots`, `Status Semantics`, and `Human Review Policy` | Show the design of a compact daily review packet | Capture the artifact list, review-state meanings, and manual-review boundary | Exact local output roots if they reveal machine paths; stale/demo rows unless explicitly labeled | “The product direction organizes complex research artifacts into a readable human review workflow.” |
| P3 | Sanitized generated daily advisory report under `outputs/reports/personal_mvp_daily_advisory_review/` | Provide a visual product artifact | Show title, no-order/no-trading notice, action wording, and 3-5 representative rows | Run ID, absolute paths, stale timestamps if misleading, private symbols/data, and any text not approved for external use | “The system can produce a compact review packet with explicit safety and interpretation guidance.” |
| P4 | [advisory_conversation.md](../advisory_conversation.md), workflow and limitations sections | Show the future AI-assisted interaction path | Crop question routing, local artifact dependency, and future richer NLP/LLM-assisted explanation statement | Example user content, private questions, absolute paths | “A conversational research experience can be added on top of governed artifacts without turning the interface into an execution system.” |

The currently available daily advisory artifact is stale and `DEMO_ONLY`; use it only as a clearly labeled guardrail example. The currently available signal report also has text-encoding defects. Neither should be used as polished investor product proof without a later sanitized capture step.

## Capture sequence

1. Capture R1-R3 to establish repository credibility.
2. Capture A1-A2 to explain the system.
3. Capture Q1-Q4 to prove research discipline.
4. Capture E1-E4 to prove engineering and status controls.
5. Capture P1-P4 only after checking that every product artifact is readable, sanitized, fresh enough for its stated purpose, and visibly non-authorizing.

## Final screenshot approval checklist

- The source path is recorded in speaker notes.
- The crop contains the evidence needed to support the slide title.
- No absolute private path, secret, raw source payload, private reviewer identity, or full hash is visible.
- Historical Replay is labeled research validation.
- PIT is described as a hindsight-leakage control, not as universal source approval.
- The eight-layer taxonomy is primary and the fixed 12 factors are not presented as final.
- Test evidence is tied to a date/checkpoint and is not described as strategy validation.
- Advisory artifacts retain manual-review and no-order language.
- Nothing implies production readiness, profitability, broker connectivity, order execution, real buy-review, or trading authority.
