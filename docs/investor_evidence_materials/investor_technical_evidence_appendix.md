# Investor Technical Evidence Appendix

## Evidence posture

`quant-replay-system` is positioned as **AI investment research infrastructure** and a **research/advisory foundation** for China A-share stocks and ETFs.

The current repository evidence supports a deterministic quantitative research, replay, governance, and human-review base. It does not support claims of a deployed production AI model, production readiness, profitability, trading capability, validated investment returns, broker connectivity, order execution, or business/research authority.

The technical value proposition is that future AI-assisted research and explanation can be built on governed evidence, point-in-time controls, repeatable replay, explainable research artifacts, and explicit human authority boundaries.

## Historical Replay

Historical Replay reconstructs a research decision as it could have been made on a selected historical date.

The documented single-date workflow:

1. loads local market, universe, benchmark, corporate-action, and calendar context;
2. filters research inputs under the point-in-time contract;
3. builds a factor dataset;
4. produces explainable component scores and risk prechecks;
5. selects research candidates;
6. simulates declared T+1 behavior after selection;
7. measures later outcomes when valid data is supplied; and
8. writes reports, tabular exports, metadata, warnings, and audit context.

Batch Replay applies the same contract across many dates and records skipped or failed dates. Calibration and portfolio-simulation foundations compare controlled settings. Walk-forward validation separates training dates from validation and optional test dates so that deterioration outside the selection window can be observed.

**Investor meaning:** Replay is an evidence engine for asking, “What would the research process have seen and selected at the time?” It supports disciplined evaluation and explanation.

**Disclosure:** Historical Replay is research validation. Simulated trades are not orders, replay outcomes are not executed returns, and the repository does not establish profitable or production-ready strategy performance.

Primary evidence: [replay_run_orchestrator.md](../replay_run_orchestrator.md), [batch_replay.md](../batch_replay.md), and [walk_forward_validation.md](../walk_forward_validation.md).

## Point-in-Time governance

Point-in-Time, or PIT, governance prevents hindsight-rich data from leaking into an earlier decision.

The core rule is:

```text
available_time <= decision_time
```

The contract distinguishes:

| Field | Investor-language meaning |
| --- | --- |
| `event_time` | When the underlying event occurred |
| `publish_time` | When the source made the information public |
| `ingest_time` | When the system received the record |
| `available_time` | Earliest time the research process may use it |
| `revision_id` | Which source revision was available |
| `as_of_date` | Historical decision date being reconstructed |

A record may already exist in a local file but still be ineligible if it was published, corrected, or made usable after the decision time. Later prices can be used after candidate selection to simulate outcomes, but not as inputs to the earlier score.

**Investor meaning:** PIT turns a backtest from a hindsight calculation into a more disciplined reconstruction of the information boundary.

**Disclosure:** A PIT contract does not mean every current source or row has been approved as real PIT evidence. Source permission, lineage, revision, instrument status, universe membership, and quality review remain separate requirements.

Primary evidence: [data_contract.md](../data_contract.md) and [quant_research_design_pack_v0_1.md](../quant_research_design_pack_v0_1.md).

## Eight-layer taxonomy

The primary factor framework is an expandable eight-layer taxonomy:

| Layer | Canonical classification | Investor-language research domain |
| --- | --- | --- |
| 1 | `L1_OPERATIONS_COMPANY_EVENTS` | Company operations, fundamentals, and company events |
| 2 | `L2_INDUSTRY_SUPPLY_DEMAND_VALUE_CHAIN_PRICES` | Industry economics, supply/demand, value chains, and price transmission |
| 3 | `L3_MACRO_LIQUIDITY_POLICY_GLOBAL` | Macro conditions, liquidity, policy, and global context |
| 4 | `L4_CAPITAL_MARKET_INSTITUTIONS_SUPPLY_DEMAND` | Institutional flows and capital-market supply/demand |
| 5 | `L5_TRADING_BEHAVIOR_MICROSTRUCTURE` | Trading behavior, liquidity, positioning, and microstructure |
| 6 | `L6_INFORMATION_DISCLOSURE_SENTIMENT_TRANSMISSION` | Disclosure, sentiment, and information transmission |
| 7 | `L7_EXPECTATIONS_VALUATION_PRICING_DEVIATION` | Expectations, valuation, and pricing deviations |
| 8 | `L8_RISK_EVENTS_COMPLIANCE_BOUNDARY` | Risk events, compliance, and explicit research boundaries |

A future factor definition is expected to declare units, direction, cadence, source requirements, PIT timing policy, and leakage guards. A future observation is expected to preserve entity, date, availability, value, source lineage, revision, and quality status.

**Investor meaning:** The ontology can expand across different research styles without losing a consistent governance structure.

**Disclosure:** The eight-layer taxonomy is primary. The fixed 12-factor framework is only a coverage checklist; it is not final, not the primary classification, and not a closed factor universe. Current taxonomy fixtures are synthetic/report-only classification evidence, not an active factor library or BUY/SELL logic.

Primary evidence: [factor_definition_schema_fixture.md](../factor_definition_schema_fixture.md) and [quant_research_design_pack_v0_1.md](../quant_research_design_pack_v0_1.md).

## Data governance

The repository treats data governance as a prerequisite for research claims. The documented control model includes:

- source identity and permission context;
- publication, ingestion, and availability timing;
- revision identity and source lineage;
- market and universe schemas;
- listed, delisted, ST, suspension, instrument-type, and membership context;
- snapshot quality, health, and status artifacts;
- deterministic reports and metadata;
- explicit warnings, blockers, and manual-review states.

The broader research design keeps source evidence, factor observations, replay decisions, forward labels, metrics, models, stock profiles, paper workflow, buy-review, and trading authority as separate gates.

**Investor meaning:** Data quality and authority are part of the product architecture, reducing the risk that a convenient local file or a promising metric is treated as validated investment evidence.

**Disclosure:** Much of the advanced source/evidence layer is currently contract, fixture, or report-only governance. The repository does not claim complete production data ingestion, universally accepted PIT evidence, or active production models.

Primary evidence: [data_contract.md](../data_contract.md), [data_quality.md](../data_quality.md), [snapshot_quality_gate.md](../snapshot_quality_gate.md), and [quant_research_design_pack_v0_1.md](../quant_research_design_pack_v0_1.md).

## Research workflow

The research process is an inspectable artifact chain:

```text
source and evidence context
  -> local ingestion and snapshot quality
  -> PIT-eligible features
  -> explainable scores and candidate selection
  -> Historical Replay and validation artifacts
  -> advisory semantics and review packets
  -> human review and paper-workflow context
```

Each stage can emit Markdown reports, CSV tables, JSON metadata, indexes, health checks, and status summaries. The unified local research dashboard is designed to show component state, warnings, blockers, and the next manual action without silently rerunning or repairing upstream workflows.

The local E2E smoke test connects data preparation, snapshot quality, current candidates, review handoff, paper-reporting context, reconciliation, and `research-status`. This provides evidence that the workflow components can exchange artifacts under local-only safety rules.

**Investor meaning:** The platform is designed as a governed research operating system, not a standalone score or chatbot.

**Disclosure:** The local E2E workflow uses mock or temporary data and proves integration, not investment quality, production operations, or authority.

Primary evidence: [local_research_workflow_e2e.md](../local_research_workflow_e2e.md), [local_research_dashboard.md](../local_research_dashboard.md), and [signal_advisory.md](../signal_advisory.md).

## Testing philosophy

The repository defines several validation tiers:

- **Unit and narrow checks** for formulas, validators, PIT behavior, and safety metadata.
- **Integration checks** for multi-module and artifact/report workflows.
- **End-to-end smoke checks** for the full local research workflow.
- **Slow/artifact-heavy checks** for repeated workflows, indexes, health scans, calibration, walk-forward, and batch artifacts.
- **Checkpoint gates** that record explicit test scopes and Git/text hygiene results.

The testing rules also preserve local-only operation: automated tests must not connect to brokers, place orders, require real API tokens, print secrets, or call real network APIs.

A current repository checkpoint document records a full non-slow regression run of `6705 passed, 109 deselected, 5 warnings` with zero failures or errors. That result is useful evidence of engineering discipline when labeled with its checkpoint and date.

**Investor meaning:** Validation covers calculations, workflow wiring, artifacts, platform-specific behavior, and prohibited-path checks.

**Disclosure:** Test counts are engineering evidence, not investment-performance evidence or production certification. The documented count is checkpoint-specific and should be rerun separately before any claim about current HEAD status.

Primary evidence: [testing_strategy.md](../testing_strategy.md), [local_research_workflow_e2e.md](../local_research_workflow_e2e.md), and [accepted_lineage_registry_windows_stable_directory_identity_correction_v0_1.md](../accepted_lineage_registry_windows_stable_directory_identity_correction_v0_1.md).

## Advisory and AI direction

The advisory layer converts local candidate artifacts into explainable human-review context: what to watch, why it appeared, validity, invalidation, risks, data-source caveats, and manual-confirmation status. Local single-symbol, daily review, and conversational-routing surfaces are documented.

The current conversational facade is deterministic and local; it is not an LLM system. Richer NLP or LLM-assisted explanation is a future direction that should consume governed artifacts and retain the same safety gates.

**Investor meaning:** AI can improve how a user explores and understands research without becoming an ungoverned execution authority.

**Disclosure:** Advisory labels are not orders, approvals, or validated recommendations. No live message, broker instruction, auto-order, real buy-review, or trading authority is created.

Primary evidence: [product_vision.md](../product_vision.md), [signal_advisory.md](../signal_advisory.md), [personal_mvp_daily_advisory_review.md](../personal_mvp_daily_advisory_review.md), and [advisory_conversation.md](../advisory_conversation.md).

## Technical evidence conclusion

The repository supports an investor narrative centered on governed research infrastructure: point-in-time data controls, repeatable replay, an expandable factor ontology, explainable artifacts, explicit validation tiers, and human review.

It does not support claims of production readiness, profitability, trading capability, validated investment returns, automatic order execution, or guaranteed outcomes.
