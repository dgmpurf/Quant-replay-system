# PIT Universe Evidence Review Worklist v0.1

`pit-universe-evidence-review-worklist` builds reviewer-facing worklists from PIT universe evidence helper and reviewed overlay artifacts.

It is worklist-only. It does not approve rows, export usable universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshot manifests, compute forward labels, mutate cache files, call APIs, send messages, connect to brokers, or place orders.

## Purpose

The worklist sits between the evidence completion helper and a later reviewer-supplied update CSV:

```text
pit-universe-overlay-review
-> pit-universe-evidence-completion-helper
-> pit-universe-evidence-review-worklist
-> reviewer fills local update CSV
-> pit-universe-overlay-review
```

It answers:

- Which PIT rows still need real evidence?
- Which missing fields are repeated across rows?
- Can the review be grouped by symbol and signal date?
- Which non-authoritative `suggested_*` hints are available?

The worklist never turns hints into approval evidence.

## CLI Usage

```cmd
python -m quant_replay_system.cli pit-universe-evidence-review-worklist --helper outputs\reports\point_in_time_universe_evidence_completion_helper\4cf008a09f04\pit_universe_evidence_completion_template.csv --review outputs\reports\point_in_time_universe_overlay_review\7bc8ba08bf5a\reviewed_pit_universe_overlay.csv
```

Optional:

- `--output-dir`: destination root for worklist artifacts.

Artifact views:

```cmd
python -m quant_replay_system.cli pit-universe-evidence-review-worklist-index
python -m quant_replay_system.cli pit-universe-evidence-review-worklist-health
python -m quant_replay_system.cli pit-universe-evidence-review-worklist-status
```

`research-status` also includes the latest worklist status as PIT universe preparation context. Worklist status can be `PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_NEEDS_REVIEW` while the final dashboard stage remains on a later paper workflow if paper artifacts are already more advanced.

After a reviewer completes the generated update template, use `pit-universe-evidence-update-ingestion` to validate the completed CSV before any separate manual `pit-universe-overlay-review` run:

```cmd
python -m quant_replay_system.cli pit-universe-evidence-update-ingestion --completed-updates outputs\reports\point_in_time_universe_evidence_review_worklist\1c7972988f59\pit_universe_evidence_review_update_template.csv --worklist outputs\reports\point_in_time_universe_evidence_review_worklist\1c7972988f59\pit_universe_evidence_review_worklist.csv
```

The ingestion validator writes clean review-update artifacts only. It does not apply approval, rerun overlay review, export universe files, build snapshots, run current-candidates, or compute labels. See [point_in_time_universe_evidence_update_ingestion.md](point_in_time_universe_evidence_update_ingestion.md).

## Outputs

Artifacts are written under:

```text
outputs/reports/point_in_time_universe_evidence_review_worklist/<worklist_id>/
```

Files:

- `pit_universe_evidence_review_worklist.csv`
- `pit_universe_evidence_review_symbol_summary.csv`
- `pit_universe_evidence_review_date_summary.csv`
- `pit_universe_evidence_review_update_template.csv`
- `pit_universe_evidence_review_worklist_report.md`
- `metadata.json`

## Worklist Views

The row-level worklist preserves one row per:

```text
signal_date + symbol + universe_name
```

The symbol summary groups repeated evidence work by symbol. It is useful for collecting listing, active-status, instrument, exchange, and source evidence once before applying it per signal date.

The date summary groups work by signal date. It is useful for checking point-in-time validity against the decision date.

## Index, Health, And Status

`pit-universe-evidence-review-worklist-index` discovers local worklist artifacts and records row counts, symbol/date counts, evidence gaps, future-dated hints, safety flags, and paths to the worklist CSV, update template, report, and metadata.

`pit-universe-evidence-review-worklist-health` checks that artifacts are readable and complete, that the worklist does not approve rows, that `valid_for_signal_date=true` is not set by the worklist, that `suggested_*` hints remain non-authoritative, and that no universe export, data write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, or message delivery occurred.

`pit-universe-evidence-review-worklist-status` summarizes the latest worklist. `PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_NEEDS_REVIEW` means reviewer evidence still needs to be completed; it is not a candidate-generation failure and it does not imply approval or export readiness.

## Update Template

The generated update template includes reviewer/evidence fields and PIT universe metadata fields expected by `pit-universe-overlay-review`, including:

- `review_status`
- `include_flag`
- `reviewer`
- `reviewed_at`
- `review_reason`
- `evidence_source`
- `evidence_path` or `evidence_reference`
- `listed_date_evidence`
- `delisted_date_evidence`
- `is_active_evidence`
- `survivorship_bias_resolved`
- `as_of_date`
- `name`
- `instrument_type`
- `exchange`
- `industry`
- `min_lot`
- `t_plus_rule`
- `available_time`
- `revision_id`
- `source`

The template leaves approval fields blank. It does not set `APPROVED_FOR_PIT_UNIVERSE`, `include_flag=true`, or `valid_for_signal_date=true`.

## Safety Rules

The worklist preserves:

- leading-zero symbols
- current review status
- current valid-for-signal-date state
- survivorship-bias warnings
- future-dated hint flags
- `hint_authoritative_for_pit=false`

It records:

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
- `worklist_only=true`

## Known Limitations

- Worklist artifacts do not approve PIT universe rows.
- Base-universe hints may be future-dated and remain non-authoritative.
- The workflow does not fetch missing evidence.
- The workflow does not produce usable universe inputs.
- A human must still provide review updates, validate them with `pit-universe-evidence-update-ingestion`, and then explicitly rerun `pit-universe-overlay-review`.
