# Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Metadata-Reference-Following

This workflow records report-only / diagnostic-only metadata-reference-following context for a future Tiny PIT real reviewed LOCAL_CSV package candidate flow.

It is not a real reviewed CSV package validator, not real reviewed CSV handling, not a real package candidate, not active reviewed input, not real replay input, not active replay input, not `ACTIVE_REPLAY_INPUT_READY`, not replay execution, not labels, not training, not model, not stock_profile, not paper validation, not buy-review, not performance validation, and not trading.

## CLI Flow

The report-only workflow is exposed through:

- `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following`
- `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following-index`
- `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following-health`
- `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following-status`

The core command can write a no-input synthetic declaration or inspect an explicit manifest in metadata-only modes. The CLI remains report-only and does not expose real reviewed CSV ingestion, package discovery, active input promotion, replay execution, label generation, training, model, stock_profile, paper, buy-review, broker, order, message, API, or trading behavior.

## Artifact Root

Default artifacts live under:

```text
outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following_v0_1/
```

Expected files include:

- `metadata.json`
- `metadata_reference_following_report.md`
- `package_manifest_inspection.csv`
- `metadata_reference_inspection.csv`
- `metadata_path_guard.csv`
- `forbidden_data_reference.csv`
- `available_time_metadata_inspection.csv`
- `source_hash_revision_metadata_inspection.csv`
- `reviewer_quality_limitation_metadata_inspection.csv`
- `forbidden_downstream_flags.json`
- `limitations.md`

Artifact views write index, health, and status files under sibling `index/`, `health/`, and `status/` folders inside the same manual diagnostics root.

## Inspection Levels

Supported inspection levels are:

- `NO_INPUT_SYNTHETIC_DECLARATIONS`: writes a safe no-input declaration with `CSV_READ_NONE`.
- `EXPLICIT_MANIFEST_METADATA_ONLY`: reads only the explicit top-level JSON manifest under allowed local roots and does not follow references.
- `METADATA_REFERENCES_DECLARED_ONLY`: records declared metadata references without opening referenced files.
- `METADATA_REFERENCES_FOLLOWED_METADATA_ONLY`: follows only whitelisted local JSON metadata references under explicit allowed roots.

All levels preserve `CSV_READ_NONE`. Even the highest level follows metadata-only JSON references and does not open CSV/data targets, raw document bodies, external URLs, package directories, or protected paths.

## Allowed Semantics

`references_followed=true` means the workflow followed one or more whitelisted local JSON metadata references such as source registry snapshots, reviewed file manifests, table schema manifests, row lineage manifests, available_time manifests, source hash / revision manifests, reviewer attestation manifests, quality review manifests, limitation manifests, or forbidden downstream flag manifests.

This is a metadata-only local inspection. It does not prove real PIT admissibility, source reliability, reviewer authority, row validity, package completeness, replay readiness, paper readiness, buy-review readiness, performance validation, or trading permission.

## Forbidden Behavior

The workflow must not:

- read real CSV content, headers, or row counts
- compute local byte hashes from referenced files
- follow CSV, TSV, Excel, Parquet, database, archive, model, JSONL, or binary data references
- follow raw document body references or external URLs
- read or write data/raw, data/processed, or data/cache
- create real reviewed CSV packages
- create real package candidates
- create active reviewed input candidates
- create real replay input or active replay input
- emit `ACTIVE_REPLAY_INPUT_READY`
- run replay or create replay evidence bundles, replay decisions, or replay decision freezes
- create forward labels or join future labels
- create training datasets, compute metrics, implement signal_score, train models, create active weights, or create active thresholds
- create stock_profile validation, paper validation, real buy-review eligibility, or buy_review_allowed
- validate strategy performance
- run current-candidates, build snapshots, or mutate signal_semantics
- call broker, order, message, API, LLM, external network, or trading systems

## Safe Status Vocabulary

Safe runtime statuses include:

- `NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_INPUT`
- `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCES_DECLARED_REPORT_ONLY`
- `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCES_FOLLOWED_REPORT_ONLY`
- `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_BLOCKED_BY_PATH_GUARD`
- `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_BLOCKED_BY_FORBIDDEN_DATA_REFERENCE`
- `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_BLOCKED_BY_MALFORMED_METADATA`
- `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_BLOCKED_BY_MISSING_REQUIRED_METADATA`
- `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_BLOCKED_BY_MANIFEST_SCHEMA`
- `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_BLOCKED_BY_METADATA_SCHEMA`
- `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_BLOCKED_BY_FORBIDDEN_DOWNSTREAM`
- `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_WARN_REVIEW_REQUIRED`

Statuses must not use or imply package approval, package admissibility, replay readiness, active replay input readiness, active reviewed input approval, buy-review readiness, performance validation, trading readiness, or broker/order permission.

## Views Summary

The index view discovers local metadata-reference-following artifact folders and summarizes latest artifact paths, status fields, inspection fields, blocker counts, and safety flags.

The health view verifies artifact readability, required files, required columns, safe status vocabulary, `CSV_READ_NONE`, report-only flags, metadata-only boundaries, false downstream flags, and absence of protected data writes.

The status view summarizes the latest discovered artifact and writes a compact status CSV and metadata JSON. It remains a view over report-only artifacts; it does not promote artifacts into a real package candidate or active input.

## Research-Status Context

`research-status` exposes metadata-reference-following fields as lower-priority context and preserves later `PAPER_WORKFLOW_READY` priority. It may show latest run id, runtime status, health, workflow stage, artifact and report paths, `csv_read_level`, inspection level, manifest-read/reference flags, metadata-files-followed count, blocker counts, limitation warning count, local-file-hash / external-source / PIT-admissibility flags, recommended next task, and downstream safety flags.

This context must not emit or imply `ACTIVE_REPLAY_INPUT_READY`, replay execution, labels, training, model, stock_profile, paper validation, buy-review, performance validation, current-candidates, snapshots, signal_semantics mutation, or trading.

## Safety Boundary

The hard safety boundary is:

- `csv_read_level` remains `CSV_READ_NONE`
- `local_file_hash_computed=false`
- `external_source_validated=false`
- `pit_admissibility_validated=false`
- `real_csv_consumed=false`
- `real_reviewed_csv_package_created=false`
- `real_package_candidate_created=false`
- `active_reviewed_input_candidate_created=false`
- `real_replay_input_created=false`
- `active_replay_input=false`
- `active_replay_ready=false`
- `active_replay_input_ready_emitted=false`
- `replay_execution_allowed=false`
- `buy_review_allowed=false`
- `trading_allowed=false`
- `data_raw_written=false`
- `data_processed_written=false`
- `data_cache_written=false`

## Recommended Next Task

Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Metadata-Reference-Following Post-Checkpoint Governance Audit Report-Only v0.1.
