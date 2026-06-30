# Release Checkpoint v1.74.0

v1.74.0 documents Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Metadata-Reference-Following core, artifact views, CLI, research-status integration, and checkpoint context.

## Included Work

- The metadata-reference-following core is available through `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following`.
- Artifact views are available through `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following-index`, `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following-health`, and `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following-status`.
- `research-status` exposes the latest metadata-reference-following context while preserving `PAPER_WORKFLOW_READY` priority.
- `docs/tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following.md` documents metadata-reference-following semantics and safety boundaries.
- `README.md` and `docs/local_research_dashboard.md` describe the v1.74.0 report-only workflow and research-status visibility.

## Lineage

- Previous checkpoint tag: `v1.73.0` at commit `21e3198`.
- Post-v1.73.0 commits included before this checkpoint documentation:
  - `8a91feb Add metadata reference following core report-only`
  - `7e824a6 Add metadata reference following artifact views report-only`
  - `ffecebf Add metadata reference following CLI report-only`
  - `626a61e Integrate metadata reference following research status report-only`
- v1.74.0 is intended to be created after ChatGPT review and manual commit/tag of this checkpoint documentation package.

## Expected Default / No-Input State

- Runtime status: `NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_INPUT`
- Health status: `PASS`
- Workflow stage: `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_CORE_CREATED_REPORT_ONLY`
- CSV read level: `CSV_READ_NONE`
- Report-only: `true`
- Diagnostic-only: `true`
- Real manifest read: `false`
- References declared: `false`
- References followed: `false`
- Local file hash computed: `false`
- External source validated: `false`
- PIT admissibility validated: `false`
- Real CSV consumed: `false`
- Real reviewed CSV package created: `false`
- Real package candidate created: `false`
- Active reviewed input candidate created: `false`
- Real replay input created: `false`
- Active replay input: `false`
- Active replay ready: `false`
- Active replay input ready emitted: `false`
- Replay execution allowed: `false`
- Trading allowed: `false`
- Buy-review allowed: `false`
- Data raw written: `false`
- Data processed written: `false`
- Data cache written: `false`

## Metadata-Reference-Following Semantics

`references_followed=true` means only whitelisted local JSON metadata references were followed under explicit allowed roots. It does not mean CSV files, data files, raw document bodies, external URLs, package directories, or reviewed CSV package contents were followed.

The workflow keeps `CSV_READ_NONE` in every inspection level. It does not consume CSV content, read CSV headers, count CSV rows, compute byte hashes from referenced files, validate real source availability, validate real available_time evidence, score source reliability, validate reviewer authority, or create package candidates.

## Safety Boundary

This checkpoint is report-only and diagnostic-only. It does not create or authorize:

- real CSV consumption
- CSV header or row-count inspection
- full CSV content reading
- local byte hash computation
- data-reference following
- real available_time adjudication
- source reliability scoring
- reviewer authority validation
- real reviewed CSV packages
- real package candidates
- active reviewed input candidates
- real replay input or active replay input
- `ACTIVE_REPLAY_INPUT_READY`
- replay execution
- replay evidence bundles
- replay decisions or replay decision freezes
- forward labels or future-label joins
- training datasets
- metric computation
- signal_score implementation or authorization
- model training
- active weights or active thresholds
- stock_profile validation
- paper validation
- real buy-review eligibility
- buy_review_allowed
- strategy performance validation
- current-candidates
- snapshots
- signal_semantics mutation
- broker/API/order/message/trading behavior
- data/raw, data/processed, or data/cache writes

No trading is authorized.

## Research-Status Boundary

`research-status` exposes the Tiny PIT metadata-reference-following workflow as context only. It must not override later paper workflow priority and must not emit or imply `ACTIVE_REPLAY_INPUT_READY`.

The final research-status workflow stage must remain `PAPER_WORKFLOW_READY` when later paper workflow context exists.

## Algorithm Timing Guard

The v1.59 Algorithm Timing Guard remains active:

- signal_score formula is design reference only.
- real weights are not calibrated yet.
- thresholds are not active yet.
- ML training must wait until PIT-valid factor observations and real governed forward labels exist.
- normalization, winsorization, and direction-adjusted values are inactive.
- factor IC / Rank IC / CAR / event study metrics are evaluation methods, not strategy performance validation by themselves.
- stock_profile is a validation dossier, not a trade instruction.
- paper workflow must precede real buy-review.
- buy-review does not equal trading.
- no broker/order/API/trading integration is allowed in current scope.

## Validation

Required validation for this checkpoint:

- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following_views.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following_cli.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_local_research_dashboard.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following.py tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following_views.py tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following_cli.py tests/test_local_research_dashboard.py -q`
- `.venv\Scripts\python.exe -m pytest -m "not slow" -q`

Required CLI validation:

- `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following`
- `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following-index`
- `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following-health`
- `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following-status`
- `research-status --root outputs/reports`

Observed validation evidence:

- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following.py`: 23 passed.
- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following_views.py`: 8 passed.
- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following_cli.py`: 4 passed.
- `tests/test_local_research_dashboard.py`: 324 passed.
- Combined focused suite: 359 passed.
- Full non-slow suite: 5458 passed, 109 deselected, 5 warnings.

Observed CLI evidence:

- `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following`: run id `b22752a386a9`, `NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_INPUT`, `PASS` health, `CSV_READ_NONE`, no real manifest read, no references declared, no references followed, no local file hash computed, no external source validated, no PIT admissibility validated, and all downstream safety flags false.
- `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following-index`: 1 artifact discovered, latest run id `b22752a386a9`.
- `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following-health`: `PASS`, 0 issues.
- `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following-status`: latest run id `b22752a386a9`, `PASS`, `CSV_READ_NONE`, `references_followed=false`, and downstream safety flags false.
- `research-status --root outputs/reports --config <repo>/config/default.yaml`, run from a temp working directory: metadata-reference-following context visible, latest run id `b22752a386a9`, runtime status `NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_INPUT`, health `PASS`, workflow stage `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_FOLLOWING_CORE_CREATED_REPORT_ONLY`, `CSV_READ_NONE`, `references_followed=false`, `real_csv_consumed=false`, `active_replay_input=false`, and `trading_allowed=false`.

## Known Limitations

- Metadata-reference following is limited to whitelisted local JSON metadata files.
- No real CSV package is consumed.
- No local file byte hash is computed.
- No real PIT admissibility logic is proven.
- No source reliability scoring or reviewer authority validation is performed.
- No real package candidate, active reviewed input candidate, real replay input, active replay input, replay evidence bundle, replay decision, replay decision freeze, forward label, future-label join, training dataset, metric computation, signal_score input, model training, active weight, active threshold, stock_profile validation, paper validation, real buy-review, performance validation, or trading workflow is implemented by this checkpoint.
- ChatGPT Project Source files are not created in Git, and `docs/project_sources/` remains intentionally absent.

## Recommended Next Task

Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Metadata-Reference-Following Post-Checkpoint Governance Audit Report-Only v0.1.
