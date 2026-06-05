# PIT Official Status Evidence Packet v0.1

`pit-official-status-evidence-packet` builds a report-only evidence packet for first-batch PIT universe rows.

It consolidates local source-access smoke diagnostics, prior official/public evidence discovery, local EOD market-cache context, and strict checklist/policy comparison reruns. It does not apply approvals, run PIT review, export universe files, write `data/raw` or `data/processed`, mutate cache, run `current-candidates`, build snapshots, compute forward labels, send messages, place orders, or call brokers.

## Commands

```text
python -m quant_replay_system.cli pit-official-status-evidence-packet
python -m quant_replay_system.cli pit-official-status-evidence-packet-index
python -m quant_replay_system.cli pit-official-status-evidence-packet-health
python -m quant_replay_system.cli pit-official-status-evidence-packet-status
```

Use `pit-official-status-evidence-packet-enrichment` after the diagnostics-only SZSE 1815 quotation and reviewed no-hit policy comparison probes are available. The enrichment command is also report-only; it consolidates strong official same-date quotation context and reviewed no-hit support context without approving rows or exporting universe files. See [pit_official_status_evidence_packet_enrichment.md](pit_official_status_evidence_packet_enrichment.md).

The build command defaults to the current first-batch diagnostics inputs:

- `outputs/reports/manual_diagnostics/szse_status_source_access_smoke_v0_1/`
- `outputs/reports/manual_diagnostics/codex_non_relaxed_pit_evidence_gap_acquisition_v0_1/`
- `outputs/reports/pit_evidence_policy_profile_comparison/0ef6d2f3bae6/`
- `outputs/reports/pit_evidence_checklist_validator/62e9eb747197/`
- `outputs/reports/activated_replacement_worklist_evidence_update_plan/4e268d67bd7d/`

## Evidence Strength

Evidence rows are classified as:

- `STRONG_OFFICIAL_DATE_SPECIFIC`: official and date-specific status evidence.
- `SUPPORTING_OFFICIAL_SYMBOL_LEVEL`: official symbol, listing, disclosure, or period context that is not daily proof.
- `SUPPORTING_LOCAL_EOD_CACHE`: same-day local market-cache context usable only under a reviewed EOD/post-close policy.
- `CONTEXT_ONLY`: useful context that does not close approval blockers.
- `MISSING`: required evidence still absent.

Official symbol-level context does not become daily status proof. Local cache support does not prove not-delisted, no-ST, or survivorship-bias resolution.

## Outputs

Artifacts are written under:

```text
outputs/reports/pit_official_status_evidence_packet/<packet_id>/
```

Files:

- `pit_official_status_evidence_packet.csv`
- `source_coverage_summary.csv`
- `per_symbol_date_status_evidence.csv`
- `evidence_strength_matrix.csv`
- `updated_draft_completed_updates.csv`
- `ingestion_validation_report.md`
- `checklist_validator_rerun_report.md`
- `policy_comparison_rerun_report.md`
- `report.md`
- `metadata.json`

`updated_draft_completed_updates.csv` is still a draft. Incomplete rows remain `NEEDS_MORE_EVIDENCE`, `include_flag=False`, and `survivorship_bias_resolved=False`.

Enrichment artifacts are written under `outputs/reports/pit_official_status_evidence_packet_enrichment/<enrichment_id>/`. The enrichment layer keeps `checklist_pass=false` and records remaining blockers such as reviewer no-hit acceptance, missing PIT-safe `as_of_date`, active/not-delisted evidence, stock ST/no-ST evidence, and survivorship-bias resolution.

## Research Status

`research-status` includes the latest packet status as PIT evidence-preparation context. A blocked packet means evidence is still missing; it is not a current-candidates failure, strategy failure, paper workflow failure, or trading signal.

`research-status` also includes the latest packet enrichment status when present, including source packet id, policy comparison id, official quotation count, reviewed no-hit context count, reviewer acceptance required count, checklist-pass count, remaining blocked count, report path, and next manual action.

Later paper workflow priority is preserved. If paper workflow artifacts are already more advanced, packet fields remain visible but do not override `PAPER_WORKFLOW_READY`.

## Known Limitations

- Current first-batch rows are expected to remain blocked.
- Local EOD cache is supporting context only.
- No complete official date-specific daily status source has been confirmed for all rows.
- Not-delisted, no-ST for stock rows, daily suspension/trading status, and survivorship-bias resolution may still require additional official evidence or a reviewed source policy.
- No strategy performance is validated.
