# Investor Presentation Screenshot Checklist

## Capture standard

Use a 16:9 frame, a readable zoom level, and repository-relative paths only. Crop out operating-system user names, drive letters, terminal history, secrets, credentials, full hashes, private reviewer identity, and raw source payloads. Every replay, advisory, or dashboard image should visibly retain its `demo`, `local-only`, `report-only`, `manual review`, or `no live trading` context.

Do not use a screenshot to imply production readiness, validated profitability, buy-review permission, order capability, or trading authority.

## Recommended captures

| Category | Screenshot purpose | Screen, file, or tool to capture | Recommended frame | Why it demonstrates value | Readiness note |
| --- | --- | --- | --- | --- | --- |
| Repository overview | Show product breadth and an organized engineering foundation | Code editor file explorer plus the `MVP v0.1` section of [README.md](../../README.md) | Keep `config/`, `docs/`, `src/`, and `tests/` visible; show the Included/Not included split | Demonstrates that data, replay, research, advisory, paper-review, dashboard, and validation concerns are organized in one system | Ready now; avoid showing `.env`, local data contents, or absolute paths |
| Investor architecture | Explain the product in one image | Rendered Markdown preview of [architecture_for_investor.md](architecture_for_investor.md) | Capture the five-layer diagram and one-line boundary statement | Makes the data-to-human-review value chain understandable without exposing implementation details | Ready after this package is reviewed |
| Point-in-time governance | Visualize the core trust mechanism | Rendered `Core Eligibility Rule` and timestamp table in [data_contract.md](../data_contract.md), or the matching section in [technical_appendix.md](technical_appendix.md) | Show `available_time <= decision_time` and the timestamp definitions together | Demonstrates a concrete control against hindsight leakage | Ready now; do not include local input paths |
| Research workflow | Show the governed artifact chain | Rendered `Local-Only Workflow` and `Expected Outputs` sections in [local_research_workflow_e2e.md](../local_research_workflow_e2e.md) | Crop to the sequence from data preparation through `research-status` | Demonstrates end-to-end workflow integration and audit artifacts | Ready now; label as local/mock E2E wiring, not strategy validation |
| Historical replay | Explain what the research engine reconstructs | Rendered `Purpose` and `Full Replay Flow` sections in [replay_run_orchestrator.md](../replay_run_orchestrator.md) | Show the research question and the numbered flow | Demonstrates repeatable decision reconstruction, explainable candidate selection, and simulated T+1 evaluation | Ready now; keep the no-live-trading sentence visible |
| Factor taxonomy | Show research extensibility | Rendered `Taxonomy Policy` section in [factor_definition_schema_fixture.md](../factor_definition_schema_fixture.md), or the eight-layer table in [technical_appendix.md](technical_appendix.md) | Fit all eight layers and the fixed-12 disclaimer in one frame | Demonstrates a broad, expandable research ontology rather than a narrow fixed factor list | Ready now; label taxonomy as governance/classification, not active signals |
| Advisory workflow | Show how research becomes a human-review artifact | Rendered `Purpose`, action counts, and safety contract from a sanitized demo advisory report, supported by [signal_advisory.md](../signal_advisory.md) | Show manual confirmation, `auto_order_allowed=false`, and no broker/message fields | Demonstrates explainable delivery with explicit safety and authority boundaries | Conditional: the currently available signal report is demo-only and contains text-encoding defects; do not use it as a polished deck screenshot |
| Daily review | Show an investor-readable human review packet | Markdown preview of a sanitized report under `outputs/reports/personal_mvp_daily_advisory_review/` | Show action wording, a few rows, and the no-order/no-trading notice | Demonstrates aggregation of research context into a compact review surface | Conditional: the available packet is stale and `DEMO_ONLY`; use it only as a guardrail example or regenerate later under separate authorization |
| Validation evidence | Show disciplined testing and audit practices | Rendered test-tier summary from [testing_strategy.md](../testing_strategy.md), paired later with a dated terminal capture of an authorized validation run | Include the command, date/commit identifier, pass result, and no-network context | Demonstrates that correctness, E2E wiring, artifact health, and safety boundaries are intentionally tested | Documentation is ready; obtain a fresh test result before a deck claims current suite status |
| Historical checkpoint evidence | Show that large focused validation sets have been recorded | The `Focused Validation Results` table in [release_checkpoint_v1.90.0.md](../release_checkpoint_v1.90.0.md) | Keep the checkpoint version and limitations visible | Provides historical evidence of focused validation discipline | Use only as dated historical evidence; do not present its counts as the current HEAD result |
| Research-status/dashboard | Show operational visibility across the workflow | A curated Markdown/HTML rendering of a future sanitized `research-status` or local research dashboard artifact; design reference: [local_research_dashboard.md](../local_research_dashboard.md) | Show a compact workflow summary, health states, warnings, and next manual action | Demonstrates that the system exposes state and blockers rather than hiding them | Conditional: a dashboard implementation exists, but the latest inspected artifact is `NO_DATA` and too wide for an investor slide; do not use it as the primary value screenshot |

## Suggested deck order

1. Repository overview.
2. Investor architecture.
3. Point-in-time governance.
4. Historical replay flow.
5. Eight-layer factor taxonomy.
6. Advisory and human-review surface.
7. Validation evidence.
8. Research-status/dashboard after a curated safe run is available.

## Capture quality checks

Before approving any screenshot:

- verify the artifact is generated from mock, demo, or otherwise approved presentation-safe data;
- show the date or artifact version when freshness matters;
- preserve leading-zero China A-share symbols as text;
- remove absolute local paths and machine-specific identifiers;
- confirm no credentials, API tokens, source payloads, private reviewer fields, or full hashes are visible;
- ensure advisory labels are described as review states, not recommendations or orders;
- ensure replay outcomes are described as simulated research results, not live returns;
- do not show a PASS badge without enough surrounding context to identify what passed;
- do not use a stale, `NO_DATA`, blocked, or demo artifact as evidence of production readiness.

## Screenshots to avoid

- `.env` or any secret/configuration screen;
- raw vendor data or evidence files without explicit disclosure approval;
- runtime logs containing local absolute paths;
- tables that imply validated profitability without dataset and evaluation context;
- advisory rows cropped so tightly that `DEMO_ONLY`, manual confirmation, or no-trading language disappears;
- any screen implying broker connectivity, automatic ordering, real buy-review eligibility, or trading authority.
