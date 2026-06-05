# PIT Official Status Evidence Packet Enrichment v0.1

`pit-official-status-evidence-packet-enrichment` is a report-only enrichment step for PIT official status evidence packets.

It combines the current official status evidence packet, the diagnostics-only SZSE 1815 same-date quotation probe, and the reviewed no-hit policy comparison context. It does not approve PIT rows, run PIT review, run export-readiness, run staging, export universe files, mutate active worklists, write `data/raw` or `data/processed`, mutate cache, run `current-candidates`, build snapshots, compute forward labels, send messages, connect to brokers, or place orders.

## Commands

```text
python -m quant_replay_system.cli pit-official-status-evidence-packet-enrichment
python -m quant_replay_system.cli pit-official-status-evidence-packet-enrichment-index
python -m quant_replay_system.cli pit-official-status-evidence-packet-enrichment-health
python -m quant_replay_system.cli pit-official-status-evidence-packet-enrichment-status
```

The build command defaults to the current first-batch evidence packet and diagnostics inputs:

- `outputs/reports/pit_official_status_evidence_packet/8efabe2ffe62/`
- `outputs/reports/manual_diagnostics/szse_1815_same_date_quotation_probe_v0_1/`
- `outputs/reports/pit_evidence_policy_profile_comparison/c1a75d1091c6/`

## Enrichment Semantics

The enrichment records whether each symbol/date row has:

- `strong_official_date_specific_quotation`: official same-date SZSE 1815 quotation presence.
- `reviewed_no_hit_context_supported`: reviewed no-hit context from the policy comparison.
- `reviewer_acceptance_required`: a reminder that no-hit support is policy-dependent and still needs manual reviewer acceptance.
- `prior_official_symbol_level_context`: prior official symbol/listing context from the packet draft.
- `local_eod_cache_context`: local same-day EOD market-cache context.

Official quotation presence can support date-specific traded-presence context, but it does not automatically prove not-delisted status, no-ST status, suspension status, or survivorship-bias resolution. Reviewed no-hit context remains reviewer-accepted context only.

## Outputs

Artifacts are written under:

```text
outputs/reports/pit_official_status_evidence_packet_enrichment/<enrichment_id>/
```

Files:

- `pit_official_status_evidence_packet_enrichment.csv`
- `pit_official_status_evidence_packet_enrichment_summary.csv`
- `remaining_enrichment_blockers.csv`
- `report.md`
- `metadata.json`

`checklist_pass` remains false in this workflow. Rows with remaining blocker categories stay blocked for later manual evidence review.

## Research Status

`research-status` includes the latest enrichment status as PIT evidence-preparation context. A blocked enrichment means quotation and no-hit context were consolidated but the row still lacks reviewer acceptance, complete PIT metadata, or survivorship rationale. It is not a current-candidates failure, strategy failure, paper workflow failure, or trading signal.

Later paper workflow priority is preserved. If paper workflow artifacts are already more advanced, enrichment fields remain visible but do not override `PAPER_WORKFLOW_READY`.

## Known Limitations

- Current first-batch rows are expected to remain blocked.
- Strong official same-date quotation evidence covers traded-presence context only.
- No-hit evidence is policy-dependent and requires reviewer acceptance before any approval workflow.
- This workflow does not generate clean review updates, approve rows, export universe files, or validate strategy performance.
