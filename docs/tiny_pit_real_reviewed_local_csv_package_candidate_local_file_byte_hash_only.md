# Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Local File Byte-Hash-Only

## Purpose

Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Local File Byte-Hash-Only is a report-only and diagnostic-only workflow for documenting a tightly bounded local file identity / integrity mode. It may compute a SHA-256 byte hash only for a manifest-gated local file under an allowed root and an explicit `--allow-local-file-byte-hash-only` flag.

It is not real reviewed CSV package handling, PIT admissibility validation, replay input creation, active replay input, replay execution, labels, training, model work, stock_profile validation, paper validation, buy-review, performance validation, or trading.

## CLI Flow

The report-only workflow is available through:

- `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only`
- `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only-index`
- `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only-health`
- `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only-status`

Default no-input execution produces safe no-input artifacts. Hash-only execution requires a manifest, an allowed root, and the explicit `--allow-local-file-byte-hash-only` opt-in flag.

## Artifact Root

Artifacts are written under:

```text
outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only_v0_1/
```

The workflow remains under manual diagnostics and does not write `data/raw`, `data/processed`, or `data/cache`.

## Manifest, Allowed Root, and Explicit Allow Flag Policy

Hash-only mode requires all of the following:

- a reviewed manifest reference;
- an allowed root that contains the referenced local file path;
- an explicit `--allow-local-file-byte-hash-only` flag;
- path guard checks preventing protected paths and path escape;
- safety flags proving that the file was not consumed as a package or replay input.

Without these conditions, the workflow must remain in no-input or blocked report-only status.

## File-Touch Taxonomy

The workflow reports three touch levels:

- `file_touch_level`: whether any allowed local file touch occurred.
- `csv_read_level`: whether CSV parsing was avoided. The safe byte-hash-only level is `CSV_READ_NONE`.
- `local_file_hash_level`: whether the local SHA-256 byte hash was computed.

The intended safe hash-only state is identity / integrity metadata, not semantic CSV interpretation.

## Hash Algorithm Policy

SHA-256 is the only supported hash algorithm in v0.1. The workflow does not negotiate algorithms, validate expected hashes, or compare source hashes to local file hashes.

## Hash Disclosure Policy

Full SHA-256 is recorded only in the local core `metadata.json`. Report, index, health, status, CLI, and research-status surfaces expose only the configured hash preview.

The full hash is local diagnostics metadata only and is not ChatGPT Project Source material. Failure messages and view artifacts must not echo full leaked hashes.

## Byte-Hash-Only Behavior

In hash-only mode:

- `local_file_byte_hash_computed` may be `true`.
- `local_file_byte_hash_algorithm` is `SHA-256`.
- `local_file_byte_hash_preview` may be recorded.
- `csv_read_level` remains `CSV_READ_NONE`.
- `csv_header_read=false`.
- `csv_row_count_computed=false`.
- `csv_row_count=""`.
- `csv_values_read=false`.
- `csv_full_content_read=false`.
- `real_csv_consumed=false`.

Byte-hash-only is therefore not header reading, not row counting, not CSV data-value reading, not full-content semantic reading, and not real CSV consumption.

## Path Guard Summary

The workflow must reject protected output or inspected paths under:

- `data/raw`
- `data/processed`
- `data/cache`
- `docs/project_sources`

It must also reject paths that escape the requested allowed root. It must not follow CSV/data references or inspect repository CSV/data targets outside existing test-controlled temporary fixtures.

## Empty File and Size-Limit Policy

The workflow keeps empty-file and size-limit checks as report-only guardrails. A file that fails those guardrails remains blocked or no-input context and does not become a package candidate.

## Artifact Views

The index, health, and status commands summarize only report-only artifacts:

- index discovers generated artifact directories and latest run metadata;
- health verifies required report files, preview-only disclosure, proof fields, and negative safety flags;
- status summarizes latest runtime status, health status, workflow stage, file-touch/hash levels, proof fields, report path, and next action.

The views must not recompute hashes, reopen target CSV files, create package candidates, create replay inputs, create active inputs, or create downstream artifacts.

## Research-Status Context

`research-status` scans:

```text
outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only_v0_1/status/
```

It exposes latest run id, runtime status, health status, workflow stage, artifact/report paths, `file_touch_level`, `csv_read_level`, `local_file_hash_level`, hash preview, hash algorithm, disclosure level, whether full hash is recorded in local metadata, file size fields, negative proof fields, and safety flags. This context must preserve later `PAPER_WORKFLOW_READY` priority and must not imply `ACTIVE_REPLAY_INPUT_READY`.

Research-status does not expose the full SHA-256.

## Safety Boundary

This workflow does not:

- read CSV headers;
- count CSV rows;
- read CSV data values;
- semantically read full CSV content;
- consume CSV as package or replay input;
- follow CSV/data references;
- verify expected hashes;
- validate source_hash;
- validate revision_id;
- adjudicate real available_time;
- validate PIT admissibility;
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

- Byte-hash-only proof is local file identity / integrity metadata only.
- The full hash is local diagnostics metadata only.
- Non-core surfaces expose preview only.
- No expected_hash verification is performed.
- No source_hash or revision_id validation is performed.
- No real available_time, source reliability, or reviewer authority logic is proven.
- No real package candidate, PIT-admissible package, replay-ready input, buy-review-ready artifact, or trading-ready artifact is created.

## Recommended Next Task

After checkpoint documentation is reviewed, run ChatGPT review for manual commit/tag v1.76.0 and ChatGPT-side curated Project Source update planning.
