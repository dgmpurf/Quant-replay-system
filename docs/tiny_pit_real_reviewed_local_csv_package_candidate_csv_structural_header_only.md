# Tiny PIT Real Reviewed LOCAL_CSV Package Candidate CSV Structural Header-Only

## Purpose

Tiny PIT Real Reviewed LOCAL_CSV Package Candidate CSV Structural Header-Only is a report-only and diagnostic-only workflow for documenting a tightly bounded structural file-touch mode. It may prove that a manifest-gated local CSV header can be inspected under an explicit allowed root and explicit `--allow-csv-header-only` flag.

It is not real reviewed CSV package handling, PIT admissibility validation, replay input creation, active replay input, replay execution, labels, training, model work, stock_profile validation, paper validation, buy-review, performance validation, or trading.

## CLI Flow

The report-only workflow is available through:

- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only`
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only-index`
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only-health`
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only-status`

Default no-input execution produces safe no-input artifacts. Header-only execution requires a manifest, an allowed root, and the explicit `--allow-csv-header-only` opt-in flag.

## Artifact Root

Artifacts are written under:

```text
outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch_v0_1/
```

The workflow remains under manual diagnostics and does not write `data/raw`, `data/processed`, or `data/cache`.

## Manifest, Allowed Root, and Explicit Allow Flag Policy

Header-only mode requires all of the following:

- a reviewed manifest reference,
- an allowed root that contains the referenced local CSV path,
- an explicit `--allow-csv-header-only` flag,
- path guard checks preventing protected paths and path escape,
- safety flags proving that the CSV was not consumed as a package or replay input.

Without these conditions, the workflow must remain in no-input or blocked report-only status.

## File-Touch Taxonomy

The workflow reports three touch levels:

- `file_touch_level`: whether any allowed structural file touch occurred.
- `csv_read_level`: whether no CSV read occurred or only header-level structural metadata was read.
- `local_file_hash_level`: whether no local file byte hash was computed.

The intended safe header-only state is structural, not semantic. It may prove a header was read, but it does not inspect rows, data values, or full content.

## Header-Only Behavior

In header-only mode:

- `csv_header_read` may be `true`.
- `csv_header_column_count` may be recorded.
- `csv_row_count_computed` remains `false`.
- `csv_row_count` remains empty.
- `csv_values_read` remains `false`.
- `csv_full_content_read` remains `false`.
- `local_file_byte_hash_computed` remains `false`.
- `local_file_byte_hash_algorithm` remains empty.
- `real_csv_consumed` remains `false`.

Header-only is therefore not row counting, not data-value reading, not full-content reading, not file byte hashing, and not real CSV consumption.

## Path Guard Summary

The workflow must reject protected output or inspected paths under:

- `data/raw`
- `data/processed`
- `data/cache`
- `docs/project_sources`

It must also reject paths that escape the requested allowed root. It must not follow CSV/data references or inspect repository CSV/data targets outside existing test-controlled temporary fixtures.

## Artifact Views

The index, health, and status commands summarize only report-only artifacts:

- index discovers generated artifact directories and latest run metadata;
- health verifies required report files, proof fields, and negative safety flags;
- status summarizes latest runtime status, health status, workflow stage, file-touch levels, proof fields, report path, and next action.

The views must not create package candidates, replay inputs, active inputs, or downstream artifacts.

## Research-Status Context

`research-status` scans:

```text
outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch_v0_1/status/
```

It exposes latest run id, runtime status, health status, workflow stage, artifact/report paths, `file_touch_level`, `csv_read_level`, `local_file_hash_level`, header proof fields, negative proof fields, and safety flags. This context must preserve later `PAPER_WORKFLOW_READY` priority and must not imply `ACTIVE_REPLAY_INPUT_READY`.

## Safety Boundary

This workflow does not:

- count CSV rows;
- read CSV data values;
- read full CSV content;
- compute local file byte hashes;
- consume CSV as package or replay input;
- follow CSV/data references;
- validate real available_time;
- score source reliability;
- validate real reviewer authority;
- create real reviewed CSV packages;
- create real package candidates;
- create active reviewed input candidates;
- create real or active replay input;
- emit `ACTIVE_REPLAY_INPUT_READY`;
- run replay;
- create replay evidence bundles, replay decisions, or replay decision freezes;
- create forward labels or join future labels;
- create training datasets, metrics, signal_score, models, weights, or thresholds;
- create stock_profile validation, paper validation, buy-review eligibility, or strategy performance validation;
- call broker/API/order/message/trading systems;
- write `data/raw`, `data/processed`, or `data/cache`.

## Known Limitations

- Header-only proof is structural only.
- Header names are not PIT evidence.
- Header column count is not row count.
- No CSV data values or full content are inspected.
- No byte hash is computed.
- No real PIT, source reliability, or reviewer authority logic is proven.
- No replay-ready or trading-ready artifact is created.

## Recommended Next Task

After checkpoint documentation is reviewed, run ChatGPT review for manual commit/tag v1.75.0 and ChatGPT-side curated Project Source update planning.

