# Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Reviewer Authority / Quality / Limitation

This workflow creates report-only / diagnostic-only reviewer authority, quality status, limitation, permission, and disclosure context for a future Tiny PIT real reviewed LOCAL_CSV package candidate.

It confirms metadata presence, shape, vocabulary, and preview-only disclosure only. It does not validate reviewer authority, approve a package, override limitations, adjudicate source permission for replay/trading, validate PIT admissibility, create real package candidates, create active replay input, run replay, create labels, train models, create stock_profile or paper validation, create buy-review eligibility, or authorize trading.

## CLI Flow

Use the core command to create report-only artifacts:

```text
tiny-pit-real-reviewed-local-csv-package-candidate-reviewer-authority-quality-limitation
```

Use the artifact views to discover and summarize the latest artifacts:

```text
tiny-pit-real-reviewed-local-csv-package-candidate-reviewer-authority-quality-limitation-index
tiny-pit-real-reviewed-local-csv-package-candidate-reviewer-authority-quality-limitation-health
tiny-pit-real-reviewed-local-csv-package-candidate-reviewer-authority-quality-limitation-status
```

The default artifact root is:

```text
outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_local_csv_package_candidate_reviewer_authority_quality_limitation_v0_1/
```

## Input Model

Metadata-present mode uses a reviewer-quality manifest and reviewer-quality metadata JSON. The run is manifest-gated, allowed-root-gated, and explicit-allow-gated. The manifest declares report-only and diagnostic-only intent, requested reviewer authority, quality status, limitation review, permission review, and package promotion levels, a reviewer-quality metadata reference, reviewer, quality, limitation, permission, disclosure, forbidden-downstream, and limitation policies.

The reviewer-quality metadata JSON may declare reviewer id preview fields, reviewer role/type, attestation presence, authority-scope declaration, manual review status, quality status, quality counts, limitation count/severity/categories, permission class, legality flag, forbidden downstream flags, and limitations.

Optional metadata references are lineage context only:

- Source Hash / Revision ID / Available-Time metadata.
- Expected-Hash Verification metadata.
- Local File Byte-Hash-Only metadata.
- CSV Physical Data-Line Count-Only metadata.

Views, status, and research-status must not reread those references for validation. They summarize the current workflow artifacts only.

## Capability Taxonomy

The workflow records capability levels rather than validation or approval:

- `reviewer_authority_level`
- `quality_status_level`
- `limitation_review_level`
- `permission_review_level`
- `package_promotion_level`

The safe no-input state is:

- Runtime status: `NO_REVIEWER_QUALITY_LIMITATION_INPUT`
- Health status: `PASS`
- Reviewer authority level: `REVIEWER_AUTHORITY_NONE`
- Quality status level: `QUALITY_STATUS_NONE`
- Limitation review level: `LIMITATION_REVIEW_NONE`
- Permission review level: `PERMISSION_REVIEW_NONE`
- Package promotion level: `PACKAGE_PROMOTION_NONE`

The safe metadata-present state is:

- Runtime status: `REVIEWER_QUALITY_LIMITATION_METADATA_PRESENT_REPORT_ONLY`
- Health status: `PASS`
- Reviewer authority level: `REVIEWER_METADATA_PRESENT_ONLY`
- Quality status level: `QUALITY_METADATA_PRESENT_ONLY`
- Limitation review level: `LIMITATION_METADATA_PRESENT_ONLY`
- Permission review level: `PERMISSION_CLASS_METADATA_PRESENT_ONLY`
- Package promotion level: `PACKAGE_PROMOTION_NONE`

WARN limitation state:

- Runtime status: `REVIEWER_QUALITY_LIMITATION_WARN_LIMITATIONS_PRESENT`
- Health status: `WARN`
- WARN limitations are review context only, not package failure.

BLOCKER limitation state:

- Runtime status: `REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_BLOCKING_LIMITATION`
- Health status: `FAIL`
- BLOCKER limitations are local actionable context only, not real validator package rejection.

Forbidden permission state:

- Runtime status: `REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_FORBIDDEN_PERMISSION`
- Health status: `FAIL`
- Forbidden permission is local actionable context only, not replay/trading permission adjudication.

Forbidden downstream state:

- Runtime status: `REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_FORBIDDEN_DOWNSTREAM`
- Health status: `FAIL`
- Any forbidden downstream flag blocks this report-only context from being summarized as safe.

## Reviewer Policy

Reviewer metadata may be present. The workflow may record `reviewer_id_recorded`, `reviewer_id_preview`, `reviewer_role`, `reviewer_type`, `reviewer_role_supported`, `reviewer_attestation_present`, and `reviewer_authority_scope_declared`.

`reviewer_authority_validated` remains false. A declared reviewer scope or attestation is not authority validation, package approval, replay readiness, buy-review readiness, or trading readiness.

## Quality Policy

Quality status may be declared with supported vocabulary such as `QUALITY_METADATA_PRESENT_ONLY`, `QUALITY_STATUS_NEEDS_REVIEW`, `QUALITY_STATUS_WARN_LIMITATIONS`, `QUALITY_STATUS_BLOCKED_BY_LIMITATIONS`, `QUALITY_STATUS_BLOCKED_BY_PERMISSION`, `QUALITY_STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM`, and `QUALITY_STATUS_BLOCKED_BY_UNSAFE_METADATA`.

`quality_status_validated` remains false. Quality metadata does not imply package approval, package admissibility, PIT admissibility, replay readiness, buy-review readiness, or trading readiness.

## Limitation Policy

INFO limitations are visible and PASS-compatible. WARN limitations are WARN context. BLOCKER limitations are FAIL context. Limitation categories are safe public categories rather than long sensitive limitation text.

`limitations_overridden_by_reviewer=false` and `limitations_overridden_by_quality=false` are required. Reviewer declarations and quality declarations cannot override limitations.

## Permission / Legal Policy

`permission_class` and `legality_flag` are metadata. `permission_class_validated=false` remains required.

`public` and `public_with_terms` may be PASS-compatible. `restricted`, `private`, `illegal_or_do_not_use`, and `unknown` become fail/actionable context. Permission metadata is not replay permission, trading permission, source reliability scoring, PIT admissibility, buy-review readiness, or strategy performance validation.

## Disclosure Policy

`reviewer_id_preview` is the only reviewer-id surface for report, index, status, CLI, and research-status outputs. Full reviewer identity, secrets, private paths, long sensitive limitation text, source content, source artifact bytes, target CSV content, row values, full file text, source reliability scores, reviewer authority approval, package admissibility, replay readiness, buy-review readiness, and trading readiness must not be exposed.

## Artifact Views

The index view discovers artifacts and records latest metadata fields, safe disclosure fields, negative proof fields, and safety flags.

The health view checks required artifacts, expected columns, safe status vocabulary, warning/failure boundaries, negative proof fields, report-only flags, and forbidden downstream flags.

The status view summarizes the latest artifact and writes compact status CSV/metadata for research-status.

These views do not open source artifacts, target CSVs, or optional referenced metadata for validation.

## Research-Status Context

`research-status` exposes the latest Reviewer Authority / Quality / Limitation context, including run id, runtime status, health status, workflow stage, artifact/report paths, capability levels, reviewer metadata presence fields, reviewer id preview, quality status fields, limitation counts and categories, permission metadata, issue/warning counts, negative proof fields, safety flags, and recommended next task.

This context is lower priority than later paper workflow context. When later paper workflow evidence exists, final workflow priority remains `PAPER_WORKFLOW_READY`.

## Safety Boundary

This workflow is not:

- reviewer authority validation
- quality-to-package promotion
- limitation override
- permission or legal adjudication beyond metadata blockers
- source artifact byte reading
- source content reading
- target CSV opening
- hash recomputation
- expected_hash reverification
- available_time adjudication
- `available_time <= replay_decision_time` PIT gating
- PIT admissibility validation
- source reliability scoring
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
- Reviewer role support does not prove reviewer authority.
- Reviewer attestation presence does not approve a package.
- Quality status declaration does not approve or promote a package.
- Limitation presence does not resolve limitations.
- Permission metadata does not grant replay, buy-review, paper, performance, broker, API, order, message, or trading permission.
- No source artifact bytes, source content, target CSV content, row values, or protected data paths are opened.
- No real package candidate, active replay input, replay, labels, training, model, stock_profile, paper validation, buy-review, performance validation, or trading behavior is created.

## Recommended Next Task

After checkpoint review and manual commit/tag, the next task should be ChatGPT review for manual commit/tag v1.80.0 and ChatGPT-side curated Project Source update planning.
