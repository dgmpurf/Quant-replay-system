# Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Source Hash Revision Available-Time

This workflow creates report-only / diagnostic-only source lineage metadata context for a future Tiny PIT real reviewed LOCAL_CSV package candidate.

It confirms metadata presence, shape, parseability, and disclosure only for source hash, revision id, and available-time fields. It does not implement source validation, PIT admissibility, package acceptance, replay input creation, replay execution, labels, training, model governance, stock_profile validation, paper validation, buy-review, or trading.

## CLI Flow

Use the core command to create report-only artifacts:

```text
tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time
```

Use the artifact views to discover and summarize the latest artifacts:

```text
tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time-index
tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time-health
tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time-status
```

The default artifact root is:

```text
outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time_v0_1/
```

## Input Model

The workflow uses a source lineage manifest and a source lineage metadata JSON file. Metadata-present mode is manifest-gated, allowed-root-gated, and explicit-allow-gated.

The manifest declares:

- report-only and diagnostic-only intent.
- requested source hash, revision id, available-time, and PIT admissibility levels.
- a source lineage metadata reference.
- source hash, revision id, available-time, and timezone policies.
- forbidden downstream flags.
- limitations.

The source lineage metadata JSON may declare source id/name/type, permission class, source hash algorithm and value, source hash disclosure level, revision id, revision id type, available time, timezone policy, quality status, manual review status, forbidden downstream flags, and limitations.

Optional local metadata references, when present, are lineage context only:

- Local File Byte-Hash-Only metadata.
- Expected-Hash Verification metadata.
- CSV Physical Data-Line Count-Only metadata.

Views, status, and research-status must not reread those references for validation. They summarize the current workflow artifacts only.

## Capability Taxonomy

The workflow records capability levels rather than approval:

- `source_hash_validation_level`
- `revision_id_validation_level`
- `available_time_validation_level`
- `pit_admissibility_level`

The safe no-input state is:

- Runtime status: `NO_SOURCE_REVISION_TIME_INPUT`
- Health status: `PASS`
- Source hash validation level: `SOURCE_HASH_VALIDATION_NONE`
- Revision id validation level: `REVISION_ID_VALIDATION_NONE`
- Available-time validation level: `AVAILABLE_TIME_VALIDATION_NONE`
- PIT admissibility level: `PIT_ADMISSIBILITY_NONE`

The safe metadata-present state is:

- Runtime status: `SOURCE_REVISION_TIME_METADATA_PRESENT_REPORT_ONLY`
- Health status: `PASS`
- Source hash validation level: `SOURCE_HASH_METADATA_PRESENT_ONLY`
- Revision id validation level: `REVISION_ID_METADATA_PRESENT_ONLY`
- Available-time validation level: `AVAILABLE_TIME_METADATA_PRESENT_ONLY`
- PIT admissibility level: `PIT_ADMISSIBILITY_NONE`

The timezone warning state is:

- Runtime status: `SOURCE_REVISION_TIME_WARN_TIMEZONE_ASSUMPTION_REQUIRED`
- Health status: `WARN`
- The timezone issue is review context only, not a PIT failure.

## Source Hash Policy

Source hash handling is metadata presence and format context only:

- `source_hash_metadata_present` may be true.
- `source_hash_format_checked` may be true.
- `source_hash_algorithm_supported` may be true.
- `source_hash_algorithm` is expected to be `SHA-256` for v0.1.
- `source_hash_preview` may be exposed as a preview-only disclosure field.
- `source_hash_validated` remains false.
- `source_hash_recomputed` remains false.
- `source_artifact_opened` remains false.
- `source_content_read` remains false.

The workflow does not open source artifact bytes, read source content, recompute source hashes, compare source hashes to local file hashes, or score source reliability.

## Revision ID Policy

Revision id handling is metadata presence and type context only:

- `revision_id_metadata_present` may be true.
- `revision_id_type_supported` may be true.
- `revision_id_value_recorded` may be true.
- `revision_id_validated` remains false.
- `revision_consistency_checked` remains false.

Revision metadata is not package readiness, source acceptance, PIT admissibility, replay readiness, buy-review readiness, or trading readiness.

## Available-Time Policy

Available-time handling is parseability context only:

- `available_time_metadata_present` may be true.
- `available_time_parseable` may be true.
- `available_time_timezone_present` may be true or warning context.
- `available_time_timezone_policy` may record the declared timezone policy.
- `available_time_compared_to_decision_time` remains false.
- `available_time_validated` remains false.
- `pit_admissibility_validated` remains false.
- `pit_admissibility_level` remains `PIT_ADMISSIBILITY_NONE`.

The workflow does not compare `available_time <= replay_decision_time`, adjudicate historical availability, or decide PIT admissibility.

## Disclosure Policy

Full source hashes are local metadata only. Report, index, status, CLI, research-status, checkpoint docs, and Project Source surfaces must use preview-only source hash disclosure.

The workflow must not expose source content, source artifact bytes, target CSV content, row values, full file text, private paths, source reliability scores, reviewer approval, package admissibility, replay readiness, buy-review readiness, or trading readiness.

## Artifact Views

The index view discovers artifacts and records latest metadata fields and safety flags.

The health view checks artifact structure, expected columns, safe status vocabulary, warning/failure boundaries, negative proof fields, report-only flags, and forbidden downstream flags.

The status view summarizes the latest artifact and writes a compact status CSV/metadata payload for research-status.

These views do not open source artifacts, target CSVs, or optional referenced metadata for validation.

## Research-Status Context

`research-status` exposes the latest Source Hash / Revision ID / Available-Time context, including run id, runtime status, health status, workflow stage, artifact/report paths, validation levels, metadata-present and parseability fields, issue/warning counts, negative proof fields, safety flags, and recommended next task.

This context is lower priority than later paper workflow context. When later paper workflow evidence exists, final workflow priority remains `PAPER_WORKFLOW_READY`.

## Safety Boundary

This workflow is not:

- source artifact byte reading
- source content reading
- target CSV opening
- hash recomputation
- expected_hash reverification
- source_hash validation
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

- Metadata-present does not mean validated.
- SHA-256 format support does not prove source integrity.
- Revision id presence does not prove revision lineage.
- Available-time parseability does not prove historical availability.
- Timezone warnings require review and are not PIT failures.
- No target CSV, source artifact, source content, or protected data path is opened.
- No real reviewed package candidate is created.

## Recommended Next Task

After checkpoint review and manual commit/tag, the next task should be ChatGPT review for manual commit/tag v1.79.0 and ChatGPT-side curated Project Source update planning.
