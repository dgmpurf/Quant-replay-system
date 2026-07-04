# Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Source Artifact Byte-Hash

This workflow creates report-only / diagnostic-only source artifact byte-identity metadata for a future Tiny PIT real reviewed LOCAL_CSV package candidate.

It may stream one explicit non-CSV source artifact as opaque bytes for SHA-256 under manifest, allowed-root, and explicit-allow guards. It records byte identity and integrity context only. It does not decode or parse source content, open target CSVs, validate source/PIT/reviewer semantics, create package candidates, create replay inputs, run replay, create labels, train models, create stock_profile or paper validation, create buy-review eligibility, or authorize trading.

## CLI Flow

Use the core command to create report-only artifacts:

```text
tiny-pit-real-reviewed-local-csv-package-candidate-source-artifact-byte-hash
```

Use the artifact views to discover and summarize the latest artifacts:

```text
tiny-pit-real-reviewed-local-csv-package-candidate-source-artifact-byte-hash-index
tiny-pit-real-reviewed-local-csv-package-candidate-source-artifact-byte-hash-health
tiny-pit-real-reviewed-local-csv-package-candidate-source-artifact-byte-hash-status
```

The default artifact root is:

```text
outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash_v0_1/
```

The default status root is:

```text
outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash_v0_1/status/
```

`research-status` can expose the latest Source Artifact Byte-Hash context when status artifacts exist.

## Input Model

Hash mode is manifest-gated, allowed-root-gated, and explicit-allow-gated.

The manifest declares:

- report-only and diagnostic-only intent.
- source artifact id and declared name.
- source artifact path reference.
- requested byte-read and hash-recompute levels.
- no-read and no-validation capability levels for source content, target CSV, local file hash, expected_hash, source_hash, revision_id, available_time, PIT admissibility, source reliability, reviewer authority, package creation, active input, and replay readiness.
- source hash algorithm and optional declared source hash.
- source lineage metadata reference.
- revision id metadata reference.
- available-time metadata reference.
- full hash recording policy.
- public disclosure policy.
- forbidden downstream flags.
- limitations.

The source lineage metadata JSON is context only. It must not turn this workflow into source validation, PIT validation, package review, replay input creation, buy-review, or trading.

## Capability Taxonomy

The safe no-input state is:

- Runtime status: `NO_SOURCE_ARTIFACT_BYTE_HASH_INPUT`
- Health status: `PASS`
- Source artifact byte read level: `SOURCE_ARTIFACT_BYTE_READ_NONE`
- Source hash recompute level: `SOURCE_HASH_RECOMPUTE_NONE`
- Source content read level: `SOURCE_CONTENT_READ_NONE`
- CSV read level: `CSV_READ_NONE`
- Source hash validation level: `SOURCE_HASH_VALIDATION_NONE`
- Revision id validation level: `REVISION_ID_VALIDATION_NONE`
- Available-time validation level: `AVAILABLE_TIME_VALIDATION_NONE`
- PIT admissibility level: `PIT_ADMISSIBILITY_NONE`

The safe hash-mode states include:

- `SOURCE_ARTIFACT_BYTE_HASH_REPORT_ONLY`
- `SOURCE_ARTIFACT_BYTE_HASH_MATCHED_REPORT_ONLY`
- `SOURCE_ARTIFACT_BYTE_HASH_MISMATCHED_REPORT_ONLY`
- `SOURCE_ARTIFACT_BYTE_HASH_WARN_SOURCE_HASH_METADATA_MISSING`
- `SOURCE_ARTIFACT_BYTE_HASH_WARN_REVISION_OR_AVAILABLE_TIME_METADATA_MISSING`

Matched artifacts are `PASS`. Mismatched or metadata-warning artifacts are `WARN` / review context only, not package rejection from a real validator and not PIT failure.

FAIL / blocked states include missing allow flag, manifest schema issue, path guard, unsupported algorithm, file-size limit, forbidden extension, source content read attempt, target CSV read attempt, forbidden downstream flag, unsafe validation claim, and health failure.

## Hash Disclosure Policy

Full computed hashes are local `metadata.json` only when the explicit local-metadata policy is used:

```text
full_hash_recording_policy=LOCAL_METADATA_ONLY
disclosure_policy=PREVIEW_ONLY_PUBLIC_SURFACES
```

Report, index, health, status, CLI, research-status, dashboard, checkpoint docs, and Project Source surfaces may expose:

- `computed_source_hash_preview`
- `declared_source_hash_preview`
- `computed_source_hash_full_recorded_in_metadata`
- byte-identity match/mismatch booleans
- issue and warning counts
- safety flags

They must not expose:

- full computed source hash
- full declared source hash
- private absolute source artifact path
- source bytes or source content
- target CSV path
- target CSV header
- target CSV rows
- target CSV values
- full target CSV text

`source_artifact_path_preview` is basename-style preview context only. It is not a private path disclosure field.

## Source Artifact Byte-Hash Boundary

This workflow may stream one explicit non-CSV source artifact as opaque bytes for SHA-256 only when all guards pass.

It must keep:

- `source_content_read=false`
- `source_content_semantically_read=false`
- `target_csv_opened=false`
- `csv_header_read=false`
- `csv_values_read=false`
- `csv_full_content_read=false`
- `source_hash_validated=false`
- `revision_id_validated=false`
- `available_time_validated=false`
- `available_time_compared_to_decision_time=false`
- `pit_admissibility_validated=false`
- `source_reliability_scored=false`
- `reviewer_authority_validated=false`

`source_hash_recomputed=true` may appear only as local Source Artifact Byte-Hash metadata for this narrow opaque byte identity workflow. It is not broad source_hash validation, expected_hash reverification, source reliability scoring, or PIT admissibility.

## Artifact Views

The index view discovers generated Source Artifact Byte-Hash artifacts and records preview-only context, safety flags, and generated artifact paths.

The health view checks artifact structure, status vocabulary, safe warning/failure boundaries, public disclosure leaks, negative proof fields, report-only flags, and forbidden downstream flags.

The status view summarizes the latest artifact and writes compact status CSV/metadata for research-status.

These views read generated Source Artifact Byte-Hash artifacts only. They do not reopen source artifacts or target CSVs for new validation.

## Research-Status Context

`research-status` exposes the latest Source Artifact Byte-Hash context, including run id, runtime status, health status, workflow stage, artifact/report/metadata paths, source id, source artifact id, source artifact name preview, hash algorithm, computed and declared hash previews, byte-identity match/mismatch booleans, capability levels, issue/warning counts, negative proof fields, safety flags, and recommended next task.

This context is lower priority than later paper workflow context. When later paper workflow evidence exists, final workflow priority remains `PAPER_WORKFLOW_READY`.

## Safety Boundary

This workflow is not:

- source content reading
- target CSV opening
- target CSV header or row reading
- broad source_hash validation
- expected_hash reverification
- revision_id validation
- available_time adjudication
- `available_time <= replay_decision_time` PIT gating
- PIT admissibility validation
- source reliability scoring
- reviewer authority validation
- real reviewed CSV package creation
- real package candidate creation
- active reviewed input candidate creation
- real replay input
- active replay input
- `ACTIVE_REPLAY_INPUT_READY`
- replay execution
- replay evidence bundle creation
- replay decision or freeze creation
- forward labels or future-label joins
- training, metrics, signal_score, model, weights, or thresholds
- stock_profile validation
- paper validation
- buy-review
- strategy performance validation
- broker/API/order/message/trading behavior
- `data/raw`, `data/processed`, or `data/cache` writes

No trading is authorized.

## Known Limitations

- Byte identity context does not prove source correctness.
- A matched declared hash preview does not mean source_hash validation.
- Full hash local metadata does not make public surfaces full-hash disclosure surfaces.
- Mismatch is actionable report-only context, not real validator package rejection.
- Revision id and available-time references are metadata context only in this workflow.
- No source content, target CSV content, or protected data path is semantically consumed.

## Recommended Next Task

After checkpoint review and manual commit/tag, the next task should be `Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Source Artifact Byte-Hash Post-v1.82 Governance Audit / Next Decision Planning Report-Only v0.1`.
