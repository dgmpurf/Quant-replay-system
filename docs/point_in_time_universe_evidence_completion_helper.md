# PIT Universe Evidence Completion Helper

`pit-universe-evidence-completion-helper` builds a local evidence-completion template for reviewed point-in-time universe overlay rows.

It is evidence-completion-only. It does not approve rows, export usable universe files, write `data/raw` or `data/processed`, run `current-candidates`, build snapshot manifests, compute forward labels, mutate cache files, call APIs, send messages, connect to brokers, or place orders.

## Purpose

The helper sits between reviewed PIT overlay artifacts and later export readiness:

```text
pit-universe-overlay-review
-> pit-universe-evidence-completion-helper
-> reviewer fills evidence fields
-> pit-universe-overlay-review
-> pit-universe-overlay-export-readiness
```

It answers:

- Which rows still need reviewer/evidence fields?
- Which fields are missing for PIT approval?
- Can an existing local base universe provide non-authoritative hints?
- Are those hints future-dated relative to the signal date?

The helper never turns hints into point-in-time approval evidence.

## CLI Usage

Run with base-universe hints:

```cmd
python -m quant_replay_system.cli pit-universe-evidence-completion-helper --review outputs\reports\point_in_time_universe_overlay_review\7bc8ba08bf5a\reviewed_pit_universe_overlay.csv --base-universe data\processed\universe\416435ab80d9\raw_data_cleaned.csv
```

Run without hints:

```cmd
python -m quant_replay_system.cli pit-universe-evidence-completion-helper --review outputs\reports\point_in_time_universe_overlay_review\7bc8ba08bf5a\reviewed_pit_universe_overlay.csv
```

## Outputs

Artifacts are written under:

```text
outputs/reports/point_in_time_universe_evidence_completion_helper/<helper_id>/
```

Files:

- `pit_universe_evidence_completion_template.csv`
- `pit_universe_evidence_gap_report.md`
- `metadata.json`

The template includes current review status, evidence gap flags, optional `suggested_*` hint columns, hint safety fields, next review action, and local-only safety flags.

## Index / Health / Status

Use `pit-universe-evidence-completion-helper-index` to discover local helper artifacts:

```cmd
python -m quant_replay_system.cli pit-universe-evidence-completion-helper-index
```

The index records helper id, review id, row counts, evidence-gap counts, base-hint counts, future-dated hint counts, authoritative hint counts, approval counts, valid-for-signal-date counts, safety flags, report path, template path, metadata path, and creation time.

Use `pit-universe-evidence-completion-helper-health` to verify helper artifacts stayed template-only:

```cmd
python -m quant_replay_system.cli pit-universe-evidence-completion-helper-health
```

Health fails if helper artifacts claim approval, set `valid_for_signal_date=true`, mark hints as authoritative for PIT approval, write `data/raw` or `data/processed`, export universe files, run current-candidates, build snapshots, compute forward labels, mutate cache, call APIs, send messages, invoke brokers, place orders, or enable live trading.

Use `pit-universe-evidence-completion-helper-status` to summarize the latest helper run:

```cmd
python -m quant_replay_system.cli pit-universe-evidence-completion-helper-status
```

Expected stages include:

- `NO_PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER`
- `PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_READY`
- `PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_NEEDS_REVIEW`
- `PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_HEALTH_WARN`
- `PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_FAILED`

`PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_NEEDS_REVIEW` is expected when rows still need evidence. It is not a candidate-generation failure, not a universe export failure, and not strategy validation.

## Research-Status Integration

`research-status` includes the latest `pit-universe-evidence-completion-helper-status` as PIT universe evidence-preparation context.

The unified summary exports:

- latest helper id
- helper status/stage
- helper health status
- linked review id
- row count
- needs-evidence count
- rows-with-base-hints count
- future-dated hint count
- authoritative hint count
- helper report path
- helper next manual action

Helper context remains below later workflow layers. If paper workflow or other later artifacts are active, `research-status` preserves the later `workflow_stage` while keeping helper fields visible for audit.

## Evidence Gaps

The helper flags missing:

- `reviewer`
- `reviewed_at`
- `review_reason`
- `evidence_source`
- `evidence_path` or `evidence_reference`
- `listed_date_evidence`
- `is_active_evidence=true`
- `survivorship_bias_resolved=true`

These fields remain blank unless already present in the input review. The helper does not infer them.

## Base Universe Hints

When `--base-universe` is supplied, the helper joins hints by `symbol` and writes them with `suggested_` prefixes, such as:

- `suggested_name`
- `suggested_instrument_type`
- `suggested_exchange`
- `suggested_industry`
- `suggested_min_lot`
- `suggested_t_plus_rule`
- `suggested_is_active`
- `suggested_is_st`
- `suggested_is_suspended`
- `suggested_source`
- `suggested_revision_id`
- `suggested_available_time`

Hints are always marked:

- `hint_authoritative_for_pit=false`

If `hint_as_of_date` or `hint_available_time` is later than the signal-date decision time, the row is marked:

- `hint_is_future_dated_for_signal_date=true`

Future-dated hints must not resolve survivorship-bias warnings or approve rows.

## Safety Boundaries

The helper always records:

- `no_universe_export=true`
- `no_data_raw_write=true`
- `no_data_processed_write=true`
- `no_current_candidates_generated=true`
- `no_snapshot_built=true`
- `no_forward_labels=true`
- `cache_mutated=false`
- `network_api_called=false`
- `llm_api_called=false`
- `no_live_trading=true`
- `no_broker_api=true`
- `no_order_placement=true`
- `no_message_sent=true`
- `evidence_completion_only=true`

It does not create `APPROVED_FOR_PIT_UNIVERSE` rows and does not set `valid_for_signal_date=true`.

## Known Limitations

- Base universe hints are not point-in-time evidence.
- The helper does not validate strategy performance or market edge.
- It does not fetch missing listed-date evidence.
- It does not produce usable universe input files.
- A human must still provide evidence and rerun `pit-universe-overlay-review` before export readiness can improve.
