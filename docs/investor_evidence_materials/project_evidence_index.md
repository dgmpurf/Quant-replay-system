# Project Evidence Index

## Purpose

This index organizes repository evidence for an investor introduction to `quant-replay-system`. It is a navigation and disclosure aid, not a new technical checkpoint, authority decision, performance report, or production-readiness assessment.

The investor positioning is **AI investment research infrastructure and a research/advisory foundation**. The repository currently documents a deterministic quantitative research base and future AI-assisted explanation opportunities; it does not document a production AI model, automatic trading bot, broker system, order execution system, or guaranteed profitable strategy.

## Evidence status vocabulary

| Status | Meaning |
| --- | --- |
| Primary evidence | Original repository documentation that defines scope, behavior, or safety boundaries |
| Validation evidence | A test, checkpoint, health, or status document tied to a stated validation context |
| Derived investor view | Investor-oriented explanation built from primary evidence; useful for presentation but not a substitute for the source |
| Conditional artifact | Generated local/demo/report-only evidence that must be checked for freshness, readability, and disclosure safety before capture |

## Repository structure evidence

| Evidence source file/path | Status | What it demonstrates | Investor explanation | Limitations and disclosure notes |
| --- | --- | --- | --- | --- |
| [README.md](../../README.md), especially `MVP v0.1`, `Project Layout`, and `Design Principles` | Primary evidence | The repository separates configuration, documentation, source, tests, local/mock data, and report artifacts; it also lists included and excluded capabilities | The project is organized as a research platform with explicit data, replay, advisory, paper-review, dashboard, and validation concerns | The README states that live broker trading, real market-data ingestion, production strategy logic, and auto-order placement are not included |
| [AGENTS.md](../../AGENTS.md) | Primary evidence | Project mission, point-in-time requirement, explainable scoring principle, China A-share/ETF scope, and non-goals | The engineering mandate prioritizes research integrity and auditability over opaque automation | The current MVP statement is conservative; use the more detailed README and focused documents for later implemented foundations, without weakening the non-goals |
| `docs/` plus [testing_strategy.md](../testing_strategy.md) | Primary evidence | A broad, topic-oriented documentation system covering data, replay, factors, advisory, status, testing, and governance | Documentation is treated as part of the operating architecture, not as a marketing layer added later | File volume is not proof of product quality; presentation should select a small number of controlling documents rather than show an unreadable file wall |

## Architecture evidence

| Evidence source file/path | Status | What it demonstrates | Investor explanation | Limitations and disclosure notes |
| --- | --- | --- | --- | --- |
| [data_contract.md](../data_contract.md) | Primary evidence | Timestamp semantics, revision handling, universe snapshots, corporate actions, and the PIT eligibility rule | The data layer is designed to distinguish information that existed from information that was actually usable at a historical decision time | A contract is an engineering control, not proof that all current data is production-grade or PIT-approved |
| [replay_run_orchestrator.md](../replay_run_orchestrator.md) | Primary evidence | A single-date flow from eligible inputs through factor construction, explainable scoring, candidate selection, simulated T+1 behavior, and reporting | The replay layer reconstructs a research decision and leaves an audit trail | Uses local/mock contexts and simulated trades; it is not live trading or validated return evidence |
| [local_research_workflow_e2e.md](../local_research_workflow_e2e.md) | Primary and validation evidence | Artifact handoffs from local data preparation through candidate review, paper-reporting context, reconciliation, and `research-status` | The system is designed as an end-to-end research workflow rather than an isolated model | The smoke workflow proves wiring and safety behavior, not strategy quality or production operations |
| [local_research_dashboard.md](../local_research_dashboard.md) | Primary evidence | A unified local status view, component health, blockers, and next manual actions | Operational visibility is part of the product: missing, stale, blocked, and review-needed states remain visible | The dashboard reads local metadata and does not repair or rerun workflows; a generated dashboard must be checked before investor use |
| [architecture_for_investor.md](../investor_materials/architecture_for_investor.md) | Derived investor view | A simplified five-layer view: data, research, replay, advisory, and human review, with governance across all layers | Provides a slide-ready architecture narrative without exposing implementation details | This is derived presentation material; primary technical claims should remain traceable to the four documents above |

## Research workflow evidence

| Evidence source file/path | Status | What it demonstrates | Investor explanation | Limitations and disclosure notes |
| --- | --- | --- | --- | --- |
| [factor_dataset.md](../factor_dataset.md) | Primary evidence | Point-in-time feature construction and market/universe eligibility context | Research features are built under explicit availability and universe constraints | The document does not establish a production factor library, machine-learning model, or final score |
| [scoring_engine.md](../scoring_engine.md) | Primary evidence | Explainable component scoring and candidate-selection foundations | A reviewer can inspect named contributors rather than accept a black-box output | The scoring foundation is not a production strategy and does not establish investment quality |
| [replay_run_orchestrator.md](../replay_run_orchestrator.md) and [batch_replay.md](../batch_replay.md) | Primary evidence | Repeatable single-date and multi-date historical research workflows | The same declared research contract can be evaluated across dates with skipped/failed dates recorded | Aggregate simulated returns depend on supplied local/mock data and are not validated investment returns |
| [parameter_calibration.md](../parameter_calibration.md) and [walk_forward_validation.md](../walk_forward_validation.md) | Primary evidence | Controlled parameter comparison, explicit train/validation/test separation, and overfitting diagnostics | The research process includes mechanisms intended to expose overfitting before later promotion decisions | Heuristics and small local samples do not prove robustness, profitability, or production readiness |
| [quant_research_design_pack_v0_1.md](../quant_research_design_pack_v0_1.md) | Primary governance evidence | Separates source evidence, factor observations, replay decisions, labels, metrics, model governance, paper workflow, and buy-review gates | The research roadmap has explicit prerequisites instead of allowing a metric or fixture to become authority | Much of the later research substrate is design, schema, or report-only governance and must not be described as active production capability |

## Validation evidence

| Evidence source file/path | Status | What it demonstrates | Investor explanation | Limitations and disclosure notes |
| --- | --- | --- | --- | --- |
| [testing_strategy.md](../testing_strategy.md) | Primary evidence | Unit, integration, E2E, and slow/artifact-heavy test tiers; local-only and no-network expectations | The project has a deliberate validation philosophy for both calculations and workflow artifacts | A testing policy is not itself a pass result and does not validate investment performance |
| [local_research_workflow_e2e.md](../local_research_workflow_e2e.md) | Validation design evidence | Specific end-to-end assertions for pipeline, snapshot quality, candidates, review handoffs, paper artifacts, reconciliation, status, and safety statements | Engineering validation covers the research workflow spine and negative safety boundaries | Uses tiny mock/temp inputs and proves workflow wiring only |
| [accepted_lineage_registry_windows_stable_directory_identity_correction_v0_1.md](../accepted_lineage_registry_windows_stable_directory_identity_correction_v0_1.md), `Validation` section | Dated validation evidence | Documents focused, platform, and full non-slow test results, including a recorded `6705 passed` full non-slow run at that checkpoint | Shows that the repository records large regression gates and platform-specific validation, not only narrow happy-path tests | This is checkpoint-specific engineering evidence. It is not a current-live test run, strategy validation, production certification, or return evidence; rerun separately before claiming current suite status |
| [release_checkpoint_v1.90.0.md](../release_checkpoint_v1.90.0.md), `Focused Validation Results` section | Historical validation evidence | Records a prior focused set of fixture, views, CLI, dashboard, and combined tests | Demonstrates an established practice of tying documentation checkpoints to explicit validation scopes | Historical only; do not present its version or pass counts as the current repository state |

## Factor framework evidence

| Evidence source file/path | Status | What it demonstrates | Investor explanation | Limitations and disclosure notes |
| --- | --- | --- | --- | --- |
| [factor_definition_schema_fixture.md](../factor_definition_schema_fixture.md), `Taxonomy Policy` | Primary governance evidence | The eight canonical taxonomy layers and the status of the fixed 12-factor checklist | The research ontology spans company, industry, macro, capital flows, trading behavior, information/sentiment, valuation/expectations, and risk/compliance | The taxonomy is classification/governance context, not BUY/SELL logic. The fixture is synthetic/report-only, not an active factor library |
| [quant_research_design_pack_v0_1.md](../quant_research_design_pack_v0_1.md), Parts 2-4 and timing guards | Primary governance evidence | Expected factor-definition fields, factor-observation lineage, event/company exposure concepts, and prerequisites for labels/models | The factor framework is designed to remain expandable while preserving timing, source, and revision controls | Real observations, active weights, active thresholds, model training, and performance claims require future governed evidence |

The eight-layer taxonomy is primary. The fixed 12-factor framework is only a coverage checklist; it is not final, not the primary classification, and not a closed factor universe.

## Advisory workflow evidence

| Evidence source file/path | Status | What it demonstrates | Investor explanation | Limitations and disclosure notes |
| --- | --- | --- | --- | --- |
| [product_vision.md](../product_vision.md) | Primary product evidence | Quantitative research and advisory-first positioning, human confirmation, and later-stage automation/market expansion boundaries | The near-term product helps a user understand what to watch, why, validity, invalidation, risk, and source caveats | Future AI-assisted or automation ideas are roadmap concepts. Current outputs are not orders, approvals, or broker instructions |
| [signal_advisory.md](../signal_advisory.md) | Primary product evidence | Deterministic advisory semantics, explainability fields, local alert previews, manual confirmation, indexes, health, and status | Research candidates can be transformed into auditable review artifacts without crossing into execution | Demo inputs remain `DEMO_ONLY`; non-demo labels still require validation and human review; no message or order is sent |
| [personal_mvp_daily_advisory_review.md](../personal_mvp_daily_advisory_review.md) | Primary product evidence | A compact daily review packet with action wording, drilldown, checklist, status, health, and negative safety fields | The product direction includes an investor-understandable review surface rather than raw research files alone | Report-only, diagnostic-only, local-only, and dependent on existing artifacts; it grants no paper, buy-review, or trading authority |
| [advisory_conversation.md](../advisory_conversation.md) | Primary product evidence | A deterministic local question-routing facade and future richer NLP/LLM-assisted explanation direction | A conversational research interface can be added without changing the governed research or authority layers | Current implementation is not an LLM system, does not fetch data, and does not create execution instructions |

## Evidence use guardrails

- Present **AI investment research infrastructure** as the product direction and governed platform framing; do not imply a deployed production AI model.
- Present Historical Replay as research validation; never as executed trading history.
- Present PIT as a control against hindsight leakage; do not imply every existing source has passed real PIT approval.
- Present advisory labels as human-review states; never as orders or guaranteed recommendations.
- Present test results as engineering evidence tied to a named checkpoint; never as investment-performance validation.
- Preserve the separation among research, paper workflow, buy-review, broker access, order placement, and trading authority.
