# Reviewer No-Hit Source Coverage Acceptance v0.1

`reviewer-no-hit-source-coverage-acceptance` creates a report-only reviewer acceptance artifact for official no-hit source coverage, query windows, inference limits, and survivorship rationale.

It consumes the latest PIT official status evidence packet enrichment plus the diagnostics-only reviewer no-hit acceptance audit. It does not approve PIT universe rows, run PIT review, run export-readiness, run export staging, export universe files, mutate active worklists, write `data/raw` or `data/processed`, mutate cache, run `current-candidates`, build snapshots, compute forward labels, send messages, connect to brokers, or place orders.

## Commands

```text
python -m quant_replay_system.cli reviewer-no-hit-source-coverage-acceptance
python -m quant_replay_system.cli reviewer-no-hit-source-coverage-acceptance-index
python -m quant_replay_system.cli reviewer-no-hit-source-coverage-acceptance-health
python -m quant_replay_system.cli reviewer-no-hit-source-coverage-acceptance-status
```

The build command defaults to:

- `outputs/reports/pit_official_status_evidence_packet_enrichment/cb5f323d3c8c/`
- `outputs/reports/manual_diagnostics/reviewer_no_hit_source_coverage_acceptance_audit_v0_1/`
- `outputs/reports/pit_evidence_policy_profile_comparison/c1a75d1091c6/`

Optional reviewer acceptance updates can be supplied with `--reviewer-acceptance`. Accepted rows are still only supporting context and never become `APPROVED_FOR_PIT_UNIVERSE`.

## Acceptance Semantics

The workflow creates one acceptance row per signal-date, symbol, universe, and exception type:

- `DELISTING`
- `ST_RISK_WARNING`
- `SUSPENSION_RESUMPTION`
- `SURVIVORSHIP_RATIONALE`

Each row starts as `NEEDS_REVIEW`. A reviewer may mark a row `ACCEPTED_AS_SUPPORTING_CONTEXT` only with reviewer identity, review time, acceptance reason, evidence reference, explicit source coverage acceptance, explicit query window acceptance, and explicit no-hit inference acceptance. `SURVIVORSHIP_RATIONALE` rows also require a written survivorship rationale.

Accepted no-hit coverage remains supporting context. It does not create checklist-pass rows, clean review updates, approval rows, export-ready rows, or current-candidates inputs.

## Outputs

Artifacts are written under:

```text
outputs/reports/reviewer_no_hit_source_coverage_acceptance/<acceptance_id>/
```

Files:

- `reviewer_no_hit_source_coverage_acceptance.csv`
- `reviewer_no_hit_acceptance_template.csv`
- `reviewer_no_hit_source_coverage_acceptance_summary.csv`
- `source_coverage_acceptance_rules.csv`
- `query_window_acceptance_rules.csv`
- `survivorship_rationale_template.csv`
- `blocker_after_acceptance_matrix.csv`
- `report.md`
- `metadata.json`

## Research Status

`research-status` includes the latest reviewer no-hit acceptance status as PIT evidence-preparation context. It records the latest acceptance id, linked enrichment/source packet/policy comparison ids, row counts, accepted supporting-context counts, survivorship-rationale counts, checklist-pass count, remaining-blocked count, health status, report path, and next manual action.

When the status reports `REVIEWER_NO_HIT_SOURCE_COVERAGE_ACCEPTANCE_NEEDS_REVIEW`, the dashboard treats the warning as expected reviewable evidence work. If later paper workflow artifacts exist, the final dashboard stage remains on the later paper workflow and the acceptance fields remain visible for audit.

## Safety Boundaries

- No approvals are applied.
- No `APPROVED_FOR_PIT_UNIVERSE` rows are created.
- No PIT review, export-readiness, staging, universe export, snapshot build, forward labels, current-candidates generation, active worklist mutation, or cache mutation occurs.
- No `data/raw` or `data/processed` files are written.
- No live trading, broker API, automated orders, real messages, LLM/API calls, or external data fetching occurs.

## Known Limitations

- The current first-batch default is expected to remain blocked: acceptance rows require reviewer completion.
- No-hit evidence remains policy-dependent and cannot resolve survivorship by itself.
- Even accepted supporting context is not enough for approval unless later validators also have complete PIT metadata and evidence.
