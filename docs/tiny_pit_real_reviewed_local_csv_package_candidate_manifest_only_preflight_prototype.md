# Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Manifest-Only Preflight Prototype

This workflow records a manifest-only / metadata-only Tiny PIT real reviewed LOCAL_CSV package candidate preflight prototype. It is report-only and diagnostic-only context for future package governance.

It is not a real reviewed CSV package, not a real package candidate, not a real PIT validator, not active reviewed input, not real replay input, not active replay input, not `ACTIVE_REPLAY_INPUT_READY`, not replay execution, not labels, not training, not model, not stock_profile, not paper validation, not buy-review, not performance validation, and not trading.

## CLI Flow

The report-only prototype is exposed through:

- `tiny-pit-real-reviewed-local-csv-package-candidate-real-preflight-prototype`
- `tiny-pit-real-reviewed-local-csv-package-candidate-real-preflight-prototype-index`
- `tiny-pit-real-reviewed-local-csv-package-candidate-real-preflight-prototype-health`
- `tiny-pit-real-reviewed-local-csv-package-candidate-real-preflight-prototype-status`

The CLI intentionally does not expose package manifest path arguments, package root arguments, reviewed CSV path arguments, allowed manifest roots, allowed package roots, or automatic discovery controls.

## Artifact Root

Default artifacts live under:

```text
outputs/reports/manual_diagnostics/tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_v0_1/
```

The latest accepted smoke run at this checkpoint is expected to use run id `fd96c4c50ea2` unless a later local smoke run regenerates equivalent report-only artifacts.

## Latest Expected State

- Status: `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_PROTOTYPE_NO_INPUT`
- Health: `PASS`
- Workflow stage: `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_MANIFEST_ONLY_PREFLIGHT_PROTOTYPE_CORE_CREATED_REPORT_ONLY`
- CSV read level: `CSV_READ_NONE`
- Real manifest read: `false`
- References followed: `false`
- Local file hash computed: `false`
- External source validated: `false`
- PIT admissibility validated: `false`
- Report-only: `true`
- Diagnostic-only: `true`
- Synthetic-only: `true`

## Manifest-Only Boundary

The prototype records synthetic declarations and manifest-shape governance only. It does not read real CSV files, read CSV headers, count CSV rows, compute local file hashes from file bytes, follow referenced manifests, inspect package roots, discover real packages, or validate real source availability.

`CSV_READ_NONE` is a hard boundary. It means the workflow has not consumed CSV content and cannot be interpreted as reviewed data acceptance.

## Safe Status Vocabulary

Safe statuses describe no-input, metadata-only, or blocked prototype states. They must not contain or imply:

- `PACKAGE_APPROVED`
- `PACKAGE_ADMISSIBLE`
- `READY_FOR_REPLAY`
- `REPLAY_INPUT_READY`
- `ACTIVE_REPLAY_INPUT_READY`
- `APPROVED_FOR_ACTIVE_INPUT`
- `TRADING_READY`
- `BUY_REVIEW_READY`

## Health, Index, And Status

The index view discovers local report artifacts only. The health view checks artifact readability, required safe fields, `CSV_READ_NONE`, and forbidden downstream flags. The status view summarizes the latest artifact and now recommends:

```text
Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Manifest-Only Preflight Prototype Post-Checkpoint Governance Audit Report-Only v0.1
```

## Research-Status Context

`research-status` exposes the latest manifest-only preflight prototype fields, including run id, status, health, workflow stage, artifact path, report path, CSV read level, metadata-only guard fields, and downstream safety flags.

This context must preserve later `PAPER_WORKFLOW_READY` priority. It must not emit or imply `ACTIVE_REPLAY_INPUT_READY`, replay execution, labels, training, stock_profile, paper validation, buy-review, performance validation, current-candidates, snapshots, signal_semantics mutation, or trading.

## Forbidden Downstream Interpretations

This checkpoint does not create or authorize:

- real CSV consumption
- real reviewed CSV packages
- real package candidates
- active reviewed input candidates
- real replay inputs
- active replay inputs
- replay execution
- replay evidence bundles
- replay decisions or decision freezes
- forward labels or future-label joins
- training datasets, metrics, signal_score, model training, active weights, or active thresholds
- stock_profile validation, paper validation, buy-review, or strategy performance validation
- current-candidates, snapshots, signal_semantics mutation, broker/API/order/message/trading
- data/raw, data/processed, or data/cache writes

## Recommended Next Task

Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Manifest-Only Preflight Prototype Post-Checkpoint Governance Audit Report-Only v0.1.
