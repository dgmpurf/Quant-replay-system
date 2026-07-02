# Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Expected-Hash Verification

## Purpose

Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Expected-Hash Verification is a report-only and diagnostic-only workflow for comparing a manifest-declared expected SHA-256 value with an existing Local File Byte-Hash-Only metadata value.

It is not target CSV opening, hash recomputation, real reviewed CSV package handling, PIT admissibility validation, replay input creation, active replay input, replay execution, labels, training, model work, stock_profile validation, paper validation, buy-review, performance validation, or trading.

## CLI Flow

The report-only workflow is available through:

- `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification`
- `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification-index`
- `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification-health`
- `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification-status`

Default no-input execution produces safe no-input artifacts. Verification mode requires an expected-hash manifest, an existing Local File Byte-Hash-Only metadata JSON path, an allowed root, and the explicit `--allow-expected-hash-verification` opt-in flag.

## Artifact Root

Artifacts are written under:

```text
outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification_v0_1/
```

The workflow remains under manual diagnostics and does not write `data/raw`, `data/processed`, or `data/cache`.

## Input Model

Verification mode uses two metadata inputs:

- an expected-hash verification manifest declaring the expected SHA-256 value, disclosure level, safety flags, and source Local File Byte-Hash-Only metadata path;
- an existing Local File Byte-Hash-Only metadata JSON containing the previously recorded local byte-hash metadata value.

The workflow compares metadata values only. It does not open the target CSV, recompute the local file byte hash, or reread source byte-hash metadata in index, health, status, CLI status, or research-status for comparison.

## Manifest, Allowed Root, and Explicit Allow Flag Policy

Verification mode requires all of the following:

- a valid expected-hash manifest;
- a matching local byte-hash metadata path;
- an allowed root that contains the manifest and metadata references;
- `requested_expected_hash_verification_level=EXPECTED_HASH_SHA256_AGAINST_LOCAL_METADATA_ONLY`;
- `requested_csv_read_level=CSV_READ_NONE`;
- `requested_local_file_hash_level=LOCAL_FILE_HASH_SHA256_METADATA_REFERENCE_ONLY`;
- explicit `--allow-expected-hash-verification`;
- path guard checks preventing protected paths and path escape;
- forbidden downstream safety flags set false.

Without these conditions, the workflow remains in no-input or blocked report-only status.

## File and Capability Taxonomy

The workflow reports these levels:

- `file_touch_level`: `FILE_TOUCH_NONE` for Expected-Hash Verification.
- `csv_read_level`: `CSV_READ_NONE`; target CSV content is not opened or parsed.
- `local_file_hash_level`: `LOCAL_FILE_HASH_NONE` for no-input, or `LOCAL_FILE_HASH_SHA256_METADATA_REFERENCE_ONLY` in verification mode.
- `expected_hash_verification_level`: `EXPECTED_HASH_VERIFICATION_NONE` for no-input, or `EXPECTED_HASH_SHA256_AGAINST_LOCAL_METADATA_ONLY` in verification mode.

## Expected-Hash Semantics

Expected-hash verification compares the manifest expected SHA-256 against the prior Local File Byte-Hash-Only metadata value only.

In verification mode:

- `expected_hash_verification_performed=true`;
- `expected_hash_verified_against_local_metadata=true`;
- `expected_hash_verified_against_source_hash=false`;
- `source_hash_validated=false`;
- `revision_id_validated=false`;
- `available_time_validated=false`;
- `pit_admissibility_validated=false`;
- `source_reliability_scored=false`;
- `reviewer_authority_validated=false`.

## Mismatch Semantics

Matched artifacts use:

- runtime status `EXPECTED_HASH_VERIFICATION_MATCHED_REPORT_ONLY`;
- health status `PASS`;
- `expected_hash_matched=true`;
- `expected_hash_mismatch=false`;
- `actionable_mismatch=false`.

Mismatched artifacts use:

- runtime status `EXPECTED_HASH_VERIFICATION_MISMATCHED_REPORT_ONLY`;
- health status `WARN`;
- `expected_hash_matched=false`;
- `expected_hash_mismatch=true`;
- `actionable_mismatch=true`.

Mismatch is not a crash, not package approval, not package rejection from a real package validator, not a source_hash validation failure, not a PIT admissibility failure, and not reviewer authority failure.

## Hash Disclosure Policy

Report, index, health, status, CLI, and research-status surfaces expose preview-only hash fields. Full expected hashes and full actual local hashes are not exposed outside the allowed local metadata policy.

Full hashes are local diagnostics metadata only and are not ChatGPT Project Source material.

## Behavior

Expected-Hash Verification may set `expected_hash_verification_performed=true`, `expected_hash_matched=true`, or `expected_hash_mismatch=true` depending on metadata comparison. It must still keep:

- `csv_read_level=CSV_READ_NONE`;
- `target_file_opened_for_expected_hash_verification=false`;
- `local_file_byte_hash_recomputed=false`;
- `csv_header_read=false`;
- `csv_row_count_computed=false`;
- `csv_row_count=""`;
- `csv_values_read=false`;
- `csv_full_content_read=false`;
- `real_csv_consumed=false`.

## Path Guard Summary

The workflow rejects protected output or inspected paths under:

- `data/raw`
- `data/processed`
- `data/cache`
- `docs/project_sources`

It also rejects paths that escape the requested allowed root and path tokens that look like secrets, credentials, auth material, or keys.

## Artifact Views

The index, health, and status commands summarize only report-only artifacts:

- index discovers generated artifact directories and latest run metadata;
- health verifies required report files, preview-only disclosure, proof fields, and negative safety flags;
- status summarizes latest runtime status, health status, workflow stage, metadata comparison levels, proof fields, report path, and next action.

The views must not recompute hashes, reopen target CSV files, reread source byte-hash metadata for comparison, reverify expected_hash, create package candidates, create replay inputs, create active inputs, or create downstream artifacts.

## Research-Status Context

`research-status` scans:

```text
outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification_v0_1/status/
```

It exposes latest run id, runtime status, health status, workflow stage, artifact/report paths, `file_touch_level`, `csv_read_level`, `local_file_hash_level`, `expected_hash_verification_level`, performed flag, algorithm, expected-hash-present flag, expected and actual hash previews, matched/mismatch/actionable-mismatch flags, issue/warning counts, negative proof fields, and safety flags.

Research-status preserves later `PAPER_WORKFLOW_READY` priority and does not expose full expected or actual hashes.

## Safety Boundary

This workflow does not:

- open target CSV files;
- recompute local file byte hashes;
- read CSV headers;
- count CSV rows;
- read CSV data values;
- semantically read full CSV content;
- consume CSV as package or replay input;
- follow CSV/data references;
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

- Expected-hash verification is metadata comparison only.
- It depends on an existing Local File Byte-Hash-Only metadata value.
- It does not prove source reliability, PIT admissibility, reviewer authority, or semantic data validity.
- Non-core surfaces expose preview-only hash fields.
- Mismatch is `WARN` / actionable context only.
- No real package candidate, PIT-admissible package, replay-ready input, buy-review-ready artifact, or trading-ready artifact is created.

## Recommended Next Task

After checkpoint documentation is reviewed, run ChatGPT review for manual commit/tag v1.77.0 and ChatGPT-side curated Project Source update planning.
