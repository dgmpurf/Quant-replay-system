# Tiny PIT Real Reviewed LOCAL_CSV Package Candidate CSV Physical Data-Line Count-Only

## Purpose

Tiny PIT Real Reviewed LOCAL_CSV Package Candidate CSV Physical Data-Line Count-Only is a report-only and diagnostic-only workflow for counting newline-delimited physical data lines in a manifest-referenced local CSV.

It excludes the first physical line as the header by explicit policy. It is not semantic CSV record counting, PIT admissibility validation, package candidate creation, replay input creation, active replay input, replay execution, labels, training, model work, stock_profile validation, paper validation, buy-review, performance validation, or trading.

## CLI Flow

The report-only workflow is available through:

- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only`
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only-index`
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only-health`
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only-status`

Default no-input execution produces safe no-input artifacts. Count mode requires a package manifest, prior CSV Structural Header-Only metadata, an allowed root, and explicit `--allow-csv-physical-data-line-count-only`.

## Artifact Root

Artifacts are written under:

```text
outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_v0_1/
```

The workflow remains under manual diagnostics and does not write `data/raw`, `data/processed`, or `data/cache`.

## Input Model

Count mode uses:

- a package manifest declaring report-only intent, count levels, one CSV file reference, prior header metadata reference, row count policy, forbidden downstream flags, and limitations;
- prior CSV Structural Header-Only metadata used only as proof that a header policy exists;
- one manifest-referenced local CSV under an explicit allowed root.

The workflow does not accept a real reviewed CSV package, create a real package candidate, or consume the CSV as replay input.

## Manifest, Allowed Root, and Explicit Allow Flag Policy

Count mode requires all of the following:

- a valid package manifest;
- exactly one `.csv` file reference;
- a prior header metadata reference;
- an allowed root containing the manifest, header metadata, and CSV reference;
- `requested_file_touch_level=CSV_PHYSICAL_DATA_LINE_COUNT_ONLY`;
- `requested_csv_read_level=CSV_PHYSICAL_DATA_LINE_COUNT_ONLY`;
- `requested_csv_physical_data_line_count_level=CSV_PHYSICAL_DATA_LINE_COUNT_ONLY`;
- `requested_local_file_hash_level=LOCAL_FILE_HASH_NONE`;
- `requested_expected_hash_verification_level=EXPECTED_HASH_VERIFICATION_NONE`;
- `row_count_policy=PHYSICAL_NON_HEADER_LINE_COUNT`;
- explicit `--allow-csv-physical-data-line-count-only`;
- path guards for protected paths and path escape;
- forbidden downstream safety flags set false.

Without these conditions, the workflow remains in no-input or blocked report-only status.

## Header Metadata Dependency

Prior header metadata is reused only as proof of the header policy. Header values are not copied or exposed by this layer.

Header metadata is not schema quality, PIT evidence, source reliability evidence, package acceptance, replay readiness, buy-review readiness, or trading permission.

## File and Capability Taxonomy

The workflow reports these levels:

- `file_touch_level`: `FILE_TOUCH_NONE` for no-input or `CSV_PHYSICAL_DATA_LINE_COUNT_ONLY` in count mode.
- `csv_read_level`: `CSV_READ_NONE` for no-input or `CSV_PHYSICAL_DATA_LINE_COUNT_ONLY` in count mode.
- `csv_physical_data_line_count_level`: `CSV_PHYSICAL_DATA_LINE_COUNT_NONE` for no-input or `CSV_PHYSICAL_DATA_LINE_COUNT_ONLY` in count mode.
- `local_file_hash_level`: `LOCAL_FILE_HASH_NONE`.
- `expected_hash_verification_level`: `EXPECTED_HASH_VERIFICATION_NONE`.

## Physical-Line Semantics

The count is newline-delimited physical data lines only. The first physical line is excluded as the header by explicit policy.

This is not semantic CSV record count. Quoted multiline CSV records are counted by physical lines, not logical CSV records.

## Behavior

In safe count mode:

- `target_csv_opened_for_physical_data_line_count` may be `true`;
- `csv_physical_data_line_count_computed=true`;
- `csv_physical_data_line_count` is an integer;
- `csv_physical_data_line_count_policy=PHYSICAL_NON_HEADER_LINE_COUNT`;
- `csv_header_line_skipped_by_policy=true` when a physical header line exists.

The same artifact must keep:

- `csv_header_read=false`;
- `csv_header_values_recorded=false`;
- `csv_values_read=false`;
- `csv_value_fields_parsed=false`;
- `csv_row_values_stored=false`;
- `csv_full_content_read=false`;
- `csv_full_content_semantically_read=false`;
- `real_csv_consumed=false`;
- `local_file_byte_hash_computed=false`;
- `local_file_byte_hash_recomputed=false`;
- `expected_hash_verification_performed=false`;
- `expected_hash_verified_against_local_metadata=false`;
- `expected_hash_verified_against_source_hash=false`;
- `source_hash_validated=false`;
- `revision_id_validated=false`;
- `available_time_validated=false`;
- `pit_admissibility_validated=false`;
- `source_reliability_scored=false`;
- `reviewer_authority_validated=false`.

## Statuses

- `NO_CSV_PHYSICAL_DATA_LINE_COUNT_INPUT`: safe no-input status, `PASS`.
- `CSV_PHYSICAL_DATA_LINE_COUNT_ONLY_REPORT_ONLY`: safe count-mode status, `PASS`.
- `CSV_PHYSICAL_DATA_LINE_COUNT_WARN_ZERO_DATA_LINES`: zero data-line warning, `WARN`.
- `CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_MISSING_ALLOW_FLAG`: missing explicit allow flag.
- `CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_MANIFEST_SCHEMA`: invalid manifest.
- `CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_PATH_GUARD`: protected path, path escape, missing allowed root, or missing file guard.
- `CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_UNSUPPORTED_LEVEL`: unsupported requested level.
- `CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_HEADER_POLICY`: invalid or unsafe prior header metadata.
- `CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_SIZE_LIMIT`: target exceeds the count-mode byte cap before scan.
- `CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_FORBIDDEN_DOWNSTREAM`: forbidden downstream flag was true.
- `CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_UNSUPPORTED_FILE_TYPE`: target reference was not `.csv`.

Blocked statuses are report-only failures and do not create package candidates, replay inputs, buy-review, or trading behavior.

## Artifact Views

The index, health, and status commands summarize only report-only artifacts:

- index discovers generated artifact directories and latest run metadata;
- health verifies required report files, policy fields, proof fields, and negative safety flags;
- status summarizes latest runtime status, health status, workflow stage, count levels, proof fields, report path, and next action.

The views must not parse CSV fields, read row values, reopen target CSV content for semantic interpretation, compute hashes, reverify expected_hash, create package candidates, create replay inputs, create active inputs, or create downstream artifacts.

## Research-Status Context

`research-status` scans:

```text
outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_v0_1/status/
```

It exposes latest run id, runtime status, health status, workflow stage, artifact/report paths, `file_touch_level`, `csv_read_level`, `local_file_hash_level`, `expected_hash_verification_level`, `csv_physical_data_line_count_level`, computed flag, count, total physical line count, policy, header dependency policy, header metadata reuse, header-line-skipped flag, zero-data-line warning, issue/warning counts, negative proof fields, and safety flags.

Research-status preserves later `PAPER_WORKFLOW_READY` priority and must not expose header values, row values, snippets, parsed fields, full-content samples, source hash values, expected hash values, local byte hash values, or target CSV text.

## Safety Boundary

This workflow does not:

- perform semantic CSV record counting;
- handle quoted multiline CSV records as one semantic record;
- parse CSV fields;
- expose header values;
- read or store row values;
- store row snippets;
- expose parsed fields or full-content samples;
- semantically read full CSV content;
- consume CSV as package or replay input;
- follow CSV/data references beyond the guarded manifest target needed for physical line scan;
- compute or recompute local file byte hashes;
- verify expected_hash;
- validate source_hash;
- validate revision_id;
- adjudicate real available_time;
- validate PIT admissibility;
- score source reliability;
- validate reviewer authority;
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

- Physical data-line count is not semantic CSV record count.
- The first physical line is excluded as the header by policy.
- Quoted multiline records are counted by physical lines, not logical CSV records.
- Zero data lines are `WARN` / context only, not package failure from a real package validator.
- Count is not package readiness, replay readiness, PIT admissibility, source reliability, reviewer authority, buy-review, performance validation, or trading permission.

## Recommended Next Task

After checkpoint documentation is reviewed, run ChatGPT review for manual commit/tag v1.78.0 and ChatGPT-side curated Project Source update planning.
