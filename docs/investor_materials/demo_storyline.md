# Investor Demo Storyline

## Demo objective

In 5-10 minutes, show how `quant-replay-system` is building a trustworthy research and advisory foundation for China A-share stocks and ETFs: governed data, point-in-time replay, expandable factor research, explainable advisory artifacts, and explicit human review.

The demo should not present live data, a production strategy, validated returns, buy-review authorization, broker connectivity, or trading capability.

## 0:00-0:45 — The problem

**Screen:** Title slide or the opening of [investor_overview.md](investor_overview.md).

**Narrative:**

“Investment research is hard to trust when we cannot tell what information was available at the time, why a candidate was selected, or whether a research output has silently become an action. This is particularly important in China A-share and ETF workflows, where universe status, source timing, suspensions, ST treatment, trading calendars, and T+1 assumptions all matter.”

**Point to land:** The product addresses research trust and workflow discipline before it addresses automation.

## 0:45-1:30 — The product vision

**Screen:** Five-layer diagram in [architecture_for_investor.md](architecture_for_investor.md).

**Narrative:**

“The vision is an AI-assisted investment research platform built on five layers: governed data, expandable research, historical replay, advisory delivery, and human review. The current system is a deterministic quantitative and advisory foundation. Future AI capabilities can help interpret and explain research, but they should sit on top of the same provenance and authority controls.”

**Point to land:** AI is the future interaction and research-assistance layer; governance and replay are the durable substrate.

## 1:30-2:45 — Show point-in-time integrity

**Screen:** `available_time <= decision_time` and timestamp definitions in [technical_appendix.md](technical_appendix.md).

**Narrative:**

“A historical record is not eligible just because it exists in a file. It must have been available by the decision time. The system distinguishes when an event happened, when it was published, when it was ingested, when it became usable, and which revision was available. That prevents a corrected or late-published record from leaking into an earlier decision.”

Then add:

“Future prices may be used after candidate selection to measure simulated outcomes, but they cannot enter the earlier research decision.”

**Point to land:** The replay is designed to reproduce the information boundary, not merely run calculations over hindsight-rich data.

## 2:45-4:00 — Show historical replay

**Screen:** `Full Replay Flow` in [replay_run_orchestrator.md](../replay_run_orchestrator.md), followed by the batch and walk-forward summary in [technical_appendix.md](technical_appendix.md).

**Narrative:**

“For a chosen decision date, the system builds a point-in-time factor dataset, creates explainable scores, selects research candidates, simulates declared T+1 behavior, measures later outcomes, and writes an audit package. Batch replay applies the same contract across dates. Calibration, portfolio simulation, and walk-forward components create a path toward disciplined out-of-sample research.”

**Boundary statement:**

“This is a research validation framework. The trades are simulated, the current data contexts are local/mock or report-only, and no profitability or production-readiness claim is being made.”

**Point to land:** Research can be repeated, inspected, and challenged.

## 4:00-5:15 — Show the factor research framework

**Screen:** Eight-layer table in [technical_appendix.md](technical_appendix.md).

**Narrative:**

“Instead of defining the platform around one small fixed factor set, the project uses an eight-layer taxonomy. It spans company events, industry economics, macro and policy, institutional capital flows, trading behavior, disclosure and sentiment, valuation and expectations, and risk/compliance boundaries.”

“A fixed 12-factor list remains only a coverage checklist. It is not the final model and not a closed research universe.”

**Point to land:** The research framework can expand while retaining consistent definitions, source requirements, timing policies, and leakage controls.

## 5:15-6:30 — Show advisory and human review

**Screen:** Purpose and safety contract in [signal_advisory.md](../signal_advisory.md), or a separately approved sanitized demo packet.

**Narrative:**

“Research candidates can be transformed into review artifacts that explain what appeared, why it appeared, when it expires, what invalidates it, and which risks or data-quality limitations apply. Labels such as WATCH or REVIEW_BUY_CANDIDATE are workflow states for a human reviewer.”

“Manual confirmation is required, auto-order is disabled, and the current system neither sends broker instructions nor creates real buy-review permission.”

**Point to land:** The product separates explanation and review from authority.

## 6:30-7:30 — Show engineering evidence

**Screen:** The E2E workflow in [local_research_workflow_e2e.md](../local_research_workflow_e2e.md) and test tiers in [testing_strategy.md](../testing_strategy.md).

**Narrative:**

“The repository connects local data preparation, snapshot quality, candidate generation, review handoff, paper-reporting artifacts, reconciliation, and a unified status view. Tests are divided into fast, integration, end-to-end, and slow artifact-heavy tiers. Safety checks explicitly verify no broker or network path is invoked in the local workflow.”

**Boundary statement:**

“This evidence proves workflow wiring and control behavior, not strategy quality.”

**Point to land:** The project has a testable operational spine, not only research notes.

## 7:30-8:45 — Separate foundations from roadmap

**Screen:** `Engineering foundations versus roadmap` in [technical_appendix.md](technical_appendix.md).

**Narrative:**

“Today, the strongest assets are the point-in-time contract, audit artifacts, replay and review workflow foundations, expandable taxonomy, and safety gates. The next milestones are reviewed production sources, real PIT-admissible observations, governed labels, stronger out-of-sample evidence, and richer AI-assisted explanation.”

“Production strategy claims, real buy-review, and any trading authority stay behind separate evidence and approval gates.”

**Point to land:** The roadmap is concrete because each future claim has a prerequisite.

## 8:45-10:00 — Close

**Screen:** Investor takeaway in [investor_overview.md](investor_overview.md).

**Narrative:**

“The goal is not to make an opaque bot trade faster. The goal is to make investment research more traceable, replayable, explainable, and reviewable. China A-share and ETF advisory is the initial product focus; the long-term platform opportunity is a governed research system that can support broader factors, richer data, AI-assisted interpretation, and later market expansion without losing the human authority boundary.”

## Presenter guardrails

Use these exact distinctions throughout the demo:

- Say “AI-assisted platform vision,” not “AI model already in production.”
- Say “research candidate” or “review state,” not “trade recommendation.”
- Say “simulated replay outcome,” not “executed return.”
- Say “local/mock or report-only foundation,” not “production data platform.”
- Say “walk-forward foundation and overfitting diagnostics,” not “proven robustness.”
- Say “manual paper-review workflow,” not “buy-review authorization.”
- Say “no broker or trading authority,” not “trading-ready.”

If asked for performance, production readiness, or authorization evidence, answer that these are future gated milestones and are not established by the current repository.
