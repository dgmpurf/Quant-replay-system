# Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight

This workflow creates report-only / diagnostic-only Preflight context for a future Tiny PIT real reviewed LOCAL_CSV package candidate. It aggregates explicit metadata references, builds an evidence reference matrix, classifies missing evidence, records blocker and warning context, and preserves negative proof fields.

It does not implement a real reviewed CSV package validator. It does not create a real package candidate, validate PIT admissibility, open CSVs or source artifacts, recompute hashes, reverify `expected_hash`, compare `available_time <= replay_decision_time`, create active input, run replay, create labels, train models, create stock_profile or paper validation, create buy-review eligibility, or authorize trading.

## CLI Flow

Use the core command to create report-only artifacts:

```text
tiny-pit-real-reviewed-local-csv-package-candidate-preflight
```

Use the artifact views to discover and summarize the latest artifacts:

```text
tiny-pit-real-reviewed-local-csv-package-candidate-preflight-index
tiny-pit-real-reviewed-local-csv-package-candidate-preflight-health
tiny-pit-real-reviewed-local-csv-package-candidate-preflight-status
```

The default artifact root is:

```text
outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_local_csv_package_candidate_preflight_v0_1/
```

The status root is:

```text
outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_local_csv_package_candidate_preflight_v0_1/status/
```

## Input Model

Metadata-context mode uses a preflight manifest JSON, optional preflight metadata JSON, and optional prior metadata artifact paths. The run is manifest-gated, allowed-root-gated, and explicit-allow-gated.

The manifest declares `preflight_id`, `declared_package_id`, package schema version, prepared-by fields, report-only and diagnostic-only intent, requested capability levels, evidence references, required evidence policy, warning policy, blocker policy, disclosure policy, forbidden downstream flags, and limitations.

`declared_package_id` is metadata only. It is not a package creation event, not real package-candidate creation, not package approval, and not replay readiness.

## Evidence Reference Policy

Required strict metadata-complete families:

- CSV Structural Header-Only metadata.
- Local File Byte-Hash-Only metadata.
- Expected-Hash Verification metadata.
- CSV Physical Data-Line Count-Only metadata.
- Source Hash / Revision ID / Available-Time metadata.
- Reviewer Authority / Quality / Limitation metadata.

Optional context:

- Metadata-Reference-Following metadata.
- Manifest-Only Preflight Prototype metadata.

References are metadata context only. Preflight may record whether a reference is declared, present, missing, warning, blocked, or unsafe. It must not open target CSVs, source artifacts, or source content, and it must not rerun or deepen prior validation.

## Capability Taxonomy

The workflow records capability levels rather than approval or validation:

- `preflight_level`
- `package_creation_level`
- `csv_read_level`
- `source_hash_validation_level`
- `revision_id_validation_level`
- `available_time_validation_level`
- `pit_admissibility_level`
- `reviewer_authority_level`
- `quality_status_level`
- `limitation_review_level`
- `permission_review_level`
- `source_reliability_level`
- `active_input_level`
- `replay_readiness_level`

Required safe boundaries include `package_creation_level=PACKAGE_CREATION_NONE`, `csv_read_level=CSV_READ_NONE`, and all source/PIT/reviewer/quality/permission/reliability/active-input/replay-readiness capability levels remaining none or metadata-only as applicable.

## Status States

Safe no-input state:

- Runtime status: `NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_INPUT`
- Health status: `PASS`
- `preflight_level=PREFLIGHT_NONE`
- `package_creation_level=PACKAGE_CREATION_NONE`
- `csv_read_level=CSV_READ_NONE`

Safe metadata-context state:

- Runtime status: `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_METADATA_CONTEXT_REPORT_ONLY`
- Health status: `PASS` when strict evidence is complete and safe
- `preflight_level=REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_METADATA_REFERENCES_ONLY`
- `package_creation_level=PACKAGE_CREATION_NONE`
- `csv_read_level=CSV_READ_NONE`

WARN states:

- `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_WARN_MISSING_OPTIONAL_EVIDENCE`
- `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_WARN_UNVALIDATED_SOURCE_HASH`
- `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_WARN_NO_AVAILABLE_TIME_PIT_GATE`

WARN means review context only. It is not package approval, not real package rejection, not PIT failure, not replay readiness, not buy-review readiness, and not trading readiness.

FAIL / blocked states:

- Missing required metadata.
- Unsafe reference metadata.
- Forbidden downstream flags.
- Reviewer / quality / limitation blocker.
- Forbidden permission.
- Unsupported validation claim.

FAIL/blocker states are local actionable context only. They are not real validator package rejection unless a separately approved real validator later consumes them.

## Artifact Set

The core writes:

- `metadata.json`
- `real_reviewed_local_csv_package_candidate_preflight_report.md`
- `limitations.md`
- `issues.csv`
- `real_reviewed_local_csv_package_candidate_preflight_summary.csv`
- `forbidden_downstream_flags.json`
- `evidence_reference_matrix.csv`

## Artifact Views

The index view discovers generated artifacts and summarizes latest runtime, health, capability, reference, issue, blocker, warning, negative-proof, and safety fields.

The health view checks generated artifact completeness, required columns, safe statuses, negative proof fields, report-only flags, forbidden downstream flags, and protected-boundary behavior.

The status view writes compact status CSV/Markdown/metadata for `research-status`.

Views read generated Preflight artifacts only. They do not reopen target CSVs, source artifacts, or referenced metadata for new validation.

## Research-Status Context

`research-status` exposes the latest Preflight context, including run id, runtime status, health status, workflow stage, artifact/report paths, preflight id, declared package id metadata, capability levels, reference counts, reference presence flags, issue/warning/blocker counts, negative proof fields, safety flags, and recommended next task.

This context is lower priority than later paper workflow context. When later paper workflow evidence exists, final workflow priority remains `PAPER_WORKFLOW_READY`.

Research-status must not expose full hashes, full reviewer identity, source content, source artifact bytes, target CSV content, header values, row values, full file text, private paths, package readiness, replay readiness, buy-review readiness, or trading readiness.

## Disclosure Policy

Public surfaces may show path previews, relative paths, hash previews already exposed by prior metadata, declared package id metadata, counts, statuses, and safe booleans. They must not print secrets, private paths, source content, target CSV content, full hashes, full reviewer identity, or sensitive limitation text.

## Safety Boundary

This workflow is not:

- real reviewed CSV package creation
- real package candidate creation
- package approval
- package admissibility
- PIT admissibility
- active reviewed input
- active replay input
- replay readiness
- source_hash validation
- source_hash recomputation
- revision_id validation
- available_time adjudication
- available_time PIT gating
- reviewer authority validation
- quality-to-package promotion
- limitation override
- permission or legal adjudication beyond metadata blockers
- source reliability scoring
- target CSV opening
- source artifact byte reading
- source content reading
- hash recomputation
- expected_hash reverification
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

- Metadata reference presence does not prove evidence quality.
- Required evidence completeness does not validate package admissibility.
- Missing optional evidence WARN states remain review context only.
- Source hash, revision id, available time, PIT, reviewer authority, quality, permission, and source reliability are not validated by this workflow.
- No source artifact bytes, source content, target CSV content, CSV headers, CSV values, row values, or protected data paths are opened.
- No real package candidate, active replay input, replay, labels, training, model, stock_profile, paper validation, buy-review, performance validation, or trading behavior is created.

## Recommended Next Task

After checkpoint review and manual commit/tag, the next task should be `Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Post-v1.81 Governance Audit / Next Decision Planning Report-Only v0.1`.
