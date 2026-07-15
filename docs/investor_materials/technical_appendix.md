# Technical Appendix for Investors

## Scope and maturity statement

`quant-replay-system` is a point-in-time historical replay research system and local signal-advisory foundation for China A-share stocks and ETFs. The technical architecture is designed for auditability, deterministic review, and later expansion.

Current evidence is based on local/mock workflows, synthetic or report-only governance fixtures, and repository validation artifacts. The system is not production-ready, is not an automatic trading bot, does not have real buy-review or trading authority, and does not establish strategy profitability.

## Architecture overview

The system can be understood as five connected layers with governance controls running across them:

| Layer | Technical role | Current foundation | Boundary |
| --- | --- | --- | --- |
| Data | Ingest and describe market, universe, corporate-action, source, and evidence records | Local/mock ingestion, manifests, snapshots, quality gates, point-in-time contracts, and governance fixtures | Real source permission and PIT admissibility require separate review |
| Research | Build eligible features, scores, rankings, and research candidates | Point-in-time factor datasets, technical indicators, explainable scoring, risk prechecks, and factor-definition governance | No production strategy logic, active factor library, or calibrated real weights is claimed |
| Replay | Reconstruct historical decisions and measure later simulated outcomes | Single-date replay, batch replay, T+1 simulation, parameter calibration, portfolio simulation, and walk-forward foundations | Research validation only; simulated trades are not live or authorized trades |
| Advisory | Convert reviewed research artifacts into explainable human-review labels and reports | Deterministic semantics, signal reports, single-symbol review, daily packets, local previews, health/status artifacts | Labels are not orders, approvals, or validated recommendations |
| Human review | Keep decisions, paper workflow, and future authority explicit and auditable | Manual review templates, paper-workflow artifacts, reconciliation, dashboards, and required confirmation fields | No real buy-review, broker, order, or trading authority exists |

Cross-cutting controls include source lineage, `available_time`, revision identity, deterministic artifact naming, health checks, status views, manual confirmation, and negative safety flags.

## Historical replay concept

Historical replay asks a constrained research question:

> Given a historical decision date, what would the system have selected using only information available at that time, and what would the later simulated outcome have been under the declared execution assumptions?

For one decision date, the documented replay flow is:

1. Load eligible market, universe, benchmark, corporate-action, and calendar context.
2. Build a point-in-time factor dataset.
3. Score rows with explainable components and risk prechecks.
4. Select research candidates.
5. Simulate T+1 entry behavior and a planned later exit.
6. Measure simple trade, benchmark, and excess-return fields when valid inputs exist.
7. Write reports, tabular exports, metadata, warnings, and audit context.

Batch replay repeats the same single-date contract across multiple dates and records skipped or failed dates. Parameter-calibration and portfolio-simulation components can compare controlled configurations. Walk-forward validation separates training dates from validation and optional test dates to make overfitting risk more visible.

These capabilities form a research-validation framework. They do not prove future performance, do not establish a production strategy, and do not create live trading capability.

## Point-in-time data validity

Point-in-time validity protects the replay from look-ahead bias. The core eligibility rule is:

```text
available_time <= decision_time
```

The distinction among timestamps matters:

| Field | Meaning |
| --- | --- |
| `event_time` | When the underlying event occurred |
| `publish_time` | When the source made the record public |
| `ingest_time` | When the system ingested the record |
| `available_time` | Earliest time the replay is allowed to use the record |
| `revision_id` | Source version for revised data |
| `as_of_date` | Historical decision date being reconstructed |

A row can exist in a local file and still be ineligible if it was published, revised, or otherwise available only after the decision time. Revised rows must carry their own availability and revision identity. When multiple eligible revisions exist, the replay uses only an eligible version according to the documented contract.

The architecture also separates decision inputs from future outcome data. Later prices may be used to simulate fills or measure outcomes after candidate selection, but they must not enter the scoring inputs for the earlier decision.

PIT eligibility is more than a timestamp comparison. The broader governance design also tracks source identity, permission scope, hashes or lineage references, universe membership, instrument status, publication timing, revisions, review status, and quality limitations. A file name, same-day price row, or report-only fixture is not by itself PIT evidence or PIT approval.

## Eight-layer factor taxonomy

The factor-definition governance model uses the following primary taxonomy:

| Layer | Canonical identifier | Investor-friendly interpretation |
| --- | --- | --- |
| 1 | `L1_OPERATIONS_COMPANY_EVENTS` | Company operations, fundamentals, and company-specific events |
| 2 | `L2_INDUSTRY_SUPPLY_DEMAND_VALUE_CHAIN_PRICES` | Industry structure, supply and demand, value chains, and price transmission |
| 3 | `L3_MACRO_LIQUIDITY_POLICY_GLOBAL` | Macro conditions, liquidity, policy, and global drivers |
| 4 | `L4_CAPITAL_MARKET_INSTITUTIONS_SUPPLY_DEMAND` | Institutional flows and capital-market supply/demand dynamics |
| 5 | `L5_TRADING_BEHAVIOR_MICROSTRUCTURE` | Trading behavior, liquidity, positioning, and market microstructure |
| 6 | `L6_INFORMATION_DISCLOSURE_SENTIMENT_TRANSMISSION` | Disclosures, news/sentiment context, and information transmission |
| 7 | `L7_EXPECTATIONS_VALUATION_PRICING_DEVIATION` | Expectations, valuation, and deviations between price and research reference points |
| 8 | `L8_RISK_EVENTS_COMPLIANCE_BOUNDARY` | Risk events, compliance constraints, and explicit veto/boundary conditions |

The taxonomy is a classification and governance structure, not a set of BUY/SELL signals. The fixed 12-factor framework is a coverage checklist only; it is not final, not the primary classification, and not a closed factor universe.

A future production factor definition is expected to identify units, directionality, update cadence, source requirements, point-in-time timing policy, and leakage guards. A future factor observation is expected to carry entity and symbol identity, observation date, availability, value, source lineage, revision, and quality status.

The repository currently documents synthetic/report-only factor-definition and factor-observation governance. It does not claim a production factor registry, active factor library, real source-backed factor observations, or active model weights.

## Research workflow

The documented end-to-end workflow is an artifact chain rather than a black-box prediction call:

```text
source and evidence review
  -> local ingestion and snapshot quality
  -> PIT-eligible factor dataset
  -> explainable scoring and candidate selection
  -> historical replay and validation artifacts
  -> advisory semantics and review packets
  -> human review and paper-workflow context
```

Each stage produces inspectable artifacts such as Markdown reports, CSV tables, JSON metadata, indexes, health checks, and status summaries. A unified `research-status` view can surface the latest local context and next manual action without rerunning or silently repairing upstream workflows.

The local end-to-end smoke workflow covers data preparation, snapshot quality, current-candidate generation, candidate health, handoff, review-template health, manual paper review, daily paper reporting, fill reconciliation, workflow status, and the unified dashboard. It is explicitly local-only and uses mock or temporary data. The smoke workflow validates wiring and safety behavior, not strategy quality.

## Engineering foundations versus roadmap

| Area | Engineering foundation documented today | Required before a stronger product claim |
| --- | --- | --- |
| Data governance | PIT schema, timing rule, revision handling, manifests, quality/status contracts, evidence-governance fixtures | Reviewed production sources, permissions, source-backed lineage, and real PIT admissibility |
| Factor research | Expandable taxonomy, point-in-time feature construction, explainable scoring foundations | Real governed observations, calibrated weights, validated thresholds, and active-library governance |
| Replay | Single-date and batch orchestration, simulated T+1 behavior, portfolio/calibration/walk-forward foundations | Admissible real data, frozen decisions, governed labels, robust OOS evidence, and manual promotion decisions |
| Advisory | Deterministic labels, reports, single-symbol and daily review surfaces, explicit safety fields | Validated research semantics, freshness operations, source-backed explanations, and separately governed delivery |
| AI experience | Architecture can support governed AI-assisted explanation | AI/ML models, evaluation, monitoring, provenance controls, and an interface that cannot bypass human authority |
| Execution | Manual and paper-review concepts remain separated from research | Separate approvals would be required; no such authority exists today |

## Technical non-claims

- Historical replay is not live trading.
- Simulated fills are not executed orders.
- Advisory labels are not trading instructions.
- Paper workflow is not real buy-review permission.
- Buy-review would not itself equal trading authority.
- Metrics, factor IC, event studies, or walk-forward heuristics do not by themselves prove profitability.
- Production readiness and validated business authority are future gates, not current states.

## Repository evidence

- [Project mission and safety rules](../../AGENTS.md)
- [Point-in-time data contract](../data_contract.md)
- [Replay run orchestrator](../replay_run_orchestrator.md)
- [Batch replay](../batch_replay.md)
- [Walk-forward validation](../walk_forward_validation.md)
- [Factor definition schema and taxonomy](../factor_definition_schema_fixture.md)
- [Quant research design boundaries](../quant_research_design_pack_v0_1.md)
- [Unified local research workflow](../local_research_workflow_e2e.md)
- [Testing strategy](../testing_strategy.md)
