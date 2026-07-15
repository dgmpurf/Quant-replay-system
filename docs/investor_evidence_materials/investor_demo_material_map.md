# Investor Demo Material Map

## Demo objective and duration

This map supports an approximately 8-minute investor demo, with room to compress to 5 minutes or expand to 10 minutes. The narrative presents `quant-replay-system` as AI investment research infrastructure and a research/advisory foundation, while retaining the project's non-trading and non-authorizing boundaries.

## Slide and evidence map

| Slide | Time | Screenshot needed | Explanation | Key investor takeaway | Required disclosure |
| ---: | ---: | --- | --- | --- | --- |
| 1 | 0:40 | R1 — README `MVP v0.1` boundary | Introduce the problem: research is hard to trust when data timing, reasoning, and action authority are blurred. Position the project around China A-share/ETF research integrity | The project starts with trustworthy research infrastructure, not automatic trading | AI is a platform direction; no production AI model, broker system, or order system is claimed |
| 2 | 0:40 | R2 and R3 — repository and curated documentation structure | Show the separation of configuration, documentation, implementation, and tests, then highlight the controlling data/replay/factor/advisory documents | The repository has an organized engineering and governance spine | Folder/document volume is not itself proof of product quality |
| 3 | 0:55 | A1 — five-layer investor architecture | Walk through data, research, replay, advisory, and human review, with governance crossing every layer | The architecture connects evidence to human judgment without collapsing into execution | The diagram is a derived investor view, not production certification |
| 4 | 1:00 | Q3 — PIT timestamp fields and eligibility rule | Explain that a record is usable only when `available_time <= decision_time`; distinguish event, publication, ingestion, availability, and revisions | PIT is a concrete defense against hindsight leakage | The contract does not mean every source or row is already PIT-approved |
| 5 | 1:00 | Q2 — Historical Replay question and flow | Show how eligible inputs become features, explainable scores, research candidates, simulated T+1 outcomes, and audit artifacts | Historical Replay makes a research decision reproducible and challengeable | Replay is research validation; simulated trades are not executed returns or trading capability |
| 6 | 0:55 | Q1 — eight-layer taxonomy | Explain the eight domains and why the framework can expand without losing source/timing governance | The factor framework is broader than a narrow fixed checklist | The eight-layer taxonomy is primary; fixed 12 factors are not final; taxonomy rows are not signals |
| 7 | 0:55 | P1 — advisory workflow and manual-confirmation fields | Show how candidate context becomes reasons, validity, invalidation, risks, and human-review labels | The product converts research complexity into an auditable review experience | Advisory labels are not recommendations, orders, buy-review approval, or trading authority |
| 8 | 0:55 | E1 and E3 — test tiers and E2E safety assertions | Explain unit/integration/E2E/slow tiers and the checks that no broker or network path is invoked | Engineering validation includes both positive workflow output and negative safety proof | Tests validate engineering behavior, not investment performance |
| 9 | 0:50 | E2 — dated checkpoint validation summary | Show the named checkpoint and focused/platform/full non-slow results | The repository records large regression gates and platform-specific evidence | The result is checkpoint-specific; do not call it a current live run or production certification |
| 10 | 0:50 | P2 or a later sanitized P3 daily review packet | Show the intended human review surface and action wording | The product direction is a compact, explainable advisory workflow for a human decision-maker | Current available packet is stale and `DEMO_ONLY`; do not use it as strategy or freshness proof |
| 11 | 0:40 | A1 or a simple foundations-versus-roadmap crop from [investor_technical_evidence_appendix.md](investor_technical_evidence_appendix.md) | Close with the roadmap: reviewed production sources, real PIT-admissible observations, stronger OOS evidence, and governed AI-assisted explanation | The future roadmap is credible because each stronger claim has an explicit prerequisite | No production readiness, profitability, validated returns, buy-review, broker, order, or trading authority exists today |

Estimated full duration: approximately 8 minutes 15 seconds.

## Five-minute compression

Use slides 1, 3, 4, 5, 6, 7, and 11. Combine slides 8-9 into one spoken engineering-proof statement and keep the checkpoint label visible.

## Ten-minute expansion

Add:

- Q4 to explain walk-forward validation and overfitting risk;
- E4 to show health/status and next-manual-action design;
- P4 to explain how a future AI-assisted conversational experience remains downstream of governed artifacts;
- a brief source trace from each slide back to [project_evidence_index.md](project_evidence_index.md).

## Presenter language

Use:

- “AI investment research infrastructure” and “AI-assisted product direction”;
- “research candidate,” “review state,” and “advisory artifact”;
- “Historical Replay research validation”;
- “simulated outcome”;
- “point-in-time eligibility” and “hindsight-leakage prevention”;
- “local/mock, synthetic, or report-only evidence” where applicable;
- “manual confirmation required.”

Avoid:

- “AI trading model in production”;
- “trade recommendation” or “order signal”;
- “live return” for replay results;
- “proven profitable,” “validated alpha,” or “guaranteed strategy”;
- “production-ready,” “broker-connected,” or “execution-enabled”;
- any claim of real buy-review, business, research, or trading authority.

## Demo stop conditions

Stop or replace a visual if:

- the source is stale, `NO_DATA`, blocked, or demo-only and the limitation is not visible;
- a screenshot exposes an absolute path, secret, source payload, private reviewer identity, or full hash;
- a generated advisory artifact has encoding defects or ambiguous action wording;
- a validation result cannot be tied to a named checkpoint or fresh authorized run;
- a replay result could be mistaken for live or validated investment performance.
