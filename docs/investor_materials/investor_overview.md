# Investor Overview

## Project vision

`quant-replay-system` is the engineering foundation for an AI-assisted investment research and advisory platform focused initially on China A-share stocks and ETFs.

The product thesis is that useful investment intelligence needs more than a prediction. It needs governed data, a record of what was knowable at the time, explainable research logic, repeatable historical testing, and an explicit human decision boundary. The project is being built around that chain.

The current system is not an automatic trading bot. It does not have live broker integration, order-placement authority, real buy-review authority, or trading authority. Its current role is local quantitative research, research validation, advisory-artifact generation, and human review support.

## The problem

Investment research often becomes difficult to trust when three questions cannot be answered:

1. Was the input actually available when the historical decision would have been made?
2. Can the reasoning behind a candidate or signal be reconstructed?
3. Is a research result being mistaken for permission to act?

China A-share and ETF research adds market-specific requirements, including trading calendars, T+1 assumptions, instrument-status checks, universe membership, suspension and ST treatment, and source-timing discipline. `quant-replay-system` treats those requirements as part of the research product rather than as after-the-fact compliance notes.

## Product proposition

The proposed platform combines five capabilities:

- **Governed research data.** Records carry availability, revision, and source context so the system can distinguish data that existed from data that was usable at a historical decision time.
- **Explainable factor research.** Research candidates can be decomposed into named components, while an expandable eight-layer taxonomy provides a durable structure for future factor coverage.
- **Historical replay.** A decision date can be reconstructed using only eligible information, followed by simulated T+1 execution and later outcome measurement. This is a research validation framework, not a representation of live trading.
- **Human-centered advisory.** Local artifacts explain what to watch, why it appeared, when the view expires, what can invalidate it, and which risks or data-quality caveats apply.
- **Audit and review surfaces.** Reports, metadata, indexes, health checks, and research-status views make each step inspectable and preserve manual review as the controlling boundary.

## Why the architecture matters

Many research products begin with a model and add governance later. This project begins with the information and authority boundaries that a trustworthy research system needs:

- point-in-time eligibility before scoring;
- source lineage and revisions before feature use;
- explainable scoring before complex models;
- replay and out-of-sample controls before performance claims;
- advisory labels before any execution-like workflow;
- manual review before any future action.

This foundation is designed to support later AI capabilities without allowing an AI interface to bypass data provenance, research validation, or human authority. Conversational explanation and richer model-assisted research are roadmap opportunities, not completed current capabilities.

## Expandable factor research framework

The primary classification is an eight-layer taxonomy spanning company operations and events; industry supply, demand, value chains, and prices; macro, liquidity, policy, and global context; institutional capital-market supply and demand; trading behavior and market microstructure; disclosure, sentiment, and information transmission; expectations, valuation, and pricing deviations; and risk, event, compliance, and boundary conditions.

This taxonomy is intended to keep the research universe expandable. A fixed 12-factor framework may be used as a coverage checklist, but it is not the final factor set, not the primary classification, and not a closed universe.

## What is completed today

The repository documents and implements a substantial local research foundation using local, mock, and report-only contexts:

- point-in-time data contracts and leakage guards;
- local ingestion, snapshot, quality, and research-artifact workflows;
- point-in-time factor-dataset construction and explainable candidate scoring;
- single-date and batch replay orchestration with simulated T+1 handling;
- parameter-calibration, portfolio-simulation, and walk-forward validation foundations;
- deterministic advisory semantics, single-symbol review, daily review packets, and local alert previews;
- manual paper-review workflow components;
- artifact indexes, health checks, status reports, and a unified local research-status view;
- unit, integration, slow, and end-to-end validation conventions.

These foundations demonstrate workflow design, auditability, and safety controls. They do not demonstrate production data readiness, a production strategy, validated profitability, an active factor library, calibrated real model weights, real advisory quality, or execution capability.

## Future product direction

The next product horizon is to convert the governed local foundation into a source-backed research platform through separately reviewed milestones:

1. Establish reviewed production data sources, permissions, lineage, revisions, and point-in-time admissibility.
2. Build real factor observations and structured event/company-exposure datasets under the eight-layer taxonomy.
3. Freeze replay decisions, govern forward labels, and perform explicit out-of-sample and walk-forward evaluation on admissible data.
4. Add richer model research and AI-assisted explanation only after the data and validation gates are satisfied.
5. Improve the advisory experience for China A-share and ETF research while preserving traceability and manual confirmation.
6. Consider later market expansion through separate source, schema, calendar, symbol, and quality reviews.

Buy-review eligibility, paper approval, and trading authority remain separate future decisions. None is granted by the current engineering foundation or by this investor-material package.

## Investor takeaway

The differentiated asset is not a claim of automatic trading. It is a governance-first research architecture intended to make quantitative and future AI-assisted investment research more explainable, replayable, and reviewable. The near-term opportunity is a decision-support product for China A-share and ETF research; the longer-term opportunity is an extensible research platform whose data, factor, replay, and advisory layers can grow without collapsing research evidence into execution authority.

## Repository evidence

- [Product vision](../product_vision.md)
- [Point-in-time data contract](../data_contract.md)
- [Replay run orchestrator](../replay_run_orchestrator.md)
- [Factor definition and taxonomy policy](../factor_definition_schema_fixture.md)
- [Unified local research workflow](../local_research_workflow_e2e.md)
- [Signal advisory contract](../signal_advisory.md)
- [Project scope and included foundations](../../README.md)
