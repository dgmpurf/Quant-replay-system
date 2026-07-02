# Release Checkpoint v1.77.0

v1.77.0 documents Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Expected-Hash Verification core, artifact views, CLI, research-status integration, and checkpoint context.

## Included Work

- The Expected-Hash Verification core is available through `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification`.
- Artifact views are available through `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification-index`, `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification-health`, and `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification-status`.
- `research-status` exposes the latest Expected-Hash Verification context while preserving `PAPER_WORKFLOW_READY` priority.
- `docs/tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification.md` documents expected-hash semantics and safety boundaries.
- `README.md` and `docs/local_research_dashboard.md` describe the v1.77.0 report-only workflow and research-status visibility.

## Lineage

- Previous checkpoint tag: `v1.76.0` at commit `09918aa`.
- Post-v1.76.0 commits included before this checkpoint documentation:
  - `717e64b Add expected-hash verification core report-only`
  - `d3dedf5 Add expected-hash verification artifact views report-only`
  - `f93766b Add expected-hash verification CLI report-only`
  - `c0d3281 Integrate expected-hash verification research status report-only`
- v1.77.0 is intended to be created after ChatGPT review and manual commit/tag of this checkpoint documentation package.

## Expected Default / No-Input State

- Runtime status: `NO_EXPECTED_HASH_VERIFICATION_INPUT`
- Health status: `PASS`
- Workflow stage: `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_EXPECTED_HASH_VERIFICATION_CORE_CREATED_REPORT_ONLY`
- Report-only: `true`
- Diagnostic-only: `true`
- File touch level: `FILE_TOUCH_NONE`
- CSV read level: `CSV_READ_NONE`
- Local file hash level: `LOCAL_FILE_HASH_NONE`
- Expected-hash verification level: `EXPECTED_HASH_VERIFICATION_NONE`
- Expected-hash verification performed: `false`
- Expected hash present: `false`
- Expected hash matched: `false`
- Expected hash mismatch: `false`
- Actionable mismatch: `false`
- Expected hash verified against local metadata: `false`
- Expected hash verified against source hash: `false`
- Source hash validated: `false`
- Revision id validated: `false`
- Available time validated: `false`
- PIT admissibility validated: `false`
- Source reliability scored: `false`
- Reviewer authority validated: `false`
- Target file opened for expected-hash verification: `false`
- Local file byte hash recomputed: `false`
- CSV header read: `false`
- CSV row count computed: `false`
- CSV row count: empty
- CSV values read: `false`
- CSV full content read: `false`
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

## Expected Matched State

- Runtime status: `EXPECTED_HASH_VERIFICATION_MATCHED_REPORT_ONLY`
- Health status: `PASS`
- Workflow stage: `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_EXPECTED_HASH_VERIFICATION_CORE_CREATED_REPORT_ONLY`
- `expected_hash_verification_performed=true`
- `expected_hash_matched=true`
- `expected_hash_mismatch=false`
- `actionable_mismatch=false`
- `expected_hash_verified_against_local_metadata=true`
- `expected_hash_verified_against_source_hash=false`
- `source_hash_validated=false`
- `revision_id_validated=false`
- `available_time_validated=false`
- `pit_admissibility_validated=false`
- `source_reliability_scored=false`
- `reviewer_authority_validated=false`
- `target_file_opened_for_expected_hash_verification=false`
- `local_file_byte_hash_recomputed=false`
- `csv_read_level=CSV_READ_NONE`
- `csv_header_read=false`
- `csv_row_count_computed=false`
- `csv_row_count=""`
- `csv_values_read=false`
- `csv_full_content_read=false`
- `real_csv_consumed=false`
- All downstream, replay, buy-review, trading, and data-write safety flags remain false.

## Expected Mismatched State

- Runtime status: `EXPECTED_HASH_VERIFICATION_MISMATCHED_REPORT_ONLY`
- Health status: `WARN`
- Workflow stage: `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_EXPECTED_HASH_VERIFICATION_CORE_CREATED_REPORT_ONLY`
- `expected_hash_verification_performed=true`
- `expected_hash_matched=false`
- `expected_hash_mismatch=true`
- `actionable_mismatch=true`
- `expected_hash_verified_against_local_metadata=true`
- `expected_hash_verified_against_source_hash=false`
- `source_hash_validated=false`
- `revision_id_validated=false`
- `available_time_validated=false`
- `pit_admissibility_validated=false`
- `source_reliability_scored=false`
- `reviewer_authority_validated=false`
- `target_file_opened_for_expected_hash_verification=false`
- `local_file_byte_hash_recomputed=false`
- `csv_read_level=CSV_READ_NONE`
- `csv_header_read=false`
- `csv_row_count_computed=false`
- `csv_row_count=""`
- `csv_values_read=false`
- `csv_full_content_read=false`
- `real_csv_consumed=false`
- All downstream, replay, buy-review, trading, and data-write safety flags remain false.

Mismatch is a `WARN` / actionable context, not a crash, package approval, package rejection from a real package validator, source_hash failure, PIT failure, or reviewer authority failure.

## Expected-Hash Verification Semantics

Expected-Hash Verification means metadata-only comparison between a manifest-declared expected SHA-256 and an existing Local File Byte-Hash-Only metadata value. It does not read target CSV content or recompute file bytes.

The workflow requires an expected-hash manifest, Local File Byte-Hash-Only metadata path, allowed root, and explicit `--allow-expected-hash-verification`.

Report, index, status, CLI, and research-status expose preview-only hash fields. Full expected hashes and full actual local hashes are not Project Source material.

## Safety Boundary

This checkpoint is report-only and diagnostic-only. It is not:

- target CSV opening
- hash recomputation
- source byte-hash metadata reread by views/status/research-status for comparison
- CSV header reading
- row counting
- CSV data value reading
- full CSV content semantic reading
- real CSV consumption as package or replay input
- CSV/data reference following
- source_hash validation
- revision_id validation
- real available_time adjudication
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

## Research-Status Boundary

`research-status` exposes the Tiny PIT Expected-Hash Verification workflow as context only. It must not expose full expected or actual hashes, override later paper workflow priority, or emit or imply `ACTIVE_REPLAY_INPUT_READY`.

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

- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification_views.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification_cli.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_local_research_dashboard.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification.py tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification_views.py tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification_cli.py tests/test_local_research_dashboard.py -q`
- `.venv\Scripts\python.exe -m pytest -m "not slow" -q`

Required CLI validation:

- `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification`
- `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification-index`
- `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification-health`
- `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification-status`
- `research-status --root <temp_reports_root> --output-dir <temp_dashboard_root> --config <repo>/config/default.yaml`

Observed validation evidence for this documentation package:

- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification.py`: 59 passed.
- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification_views.py`: 20 passed.
- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification_cli.py`: 10 passed.
- `tests/test_local_research_dashboard.py`: 333 passed.
- Combined focused suite: 422 passed.
- Full non-slow suite: 5676 passed, 109 deselected, 5 warnings.

Observed CLI evidence from a temporary working directory:

- `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification`: run id `e020ed1246dd`, `NO_EXPECTED_HASH_VERIFICATION_INPUT`, `PASS` health, `FILE_TOUCH_NONE`, `CSV_READ_NONE`, `LOCAL_FILE_HASH_NONE`, no expected-hash verification performed, no expected or actual hash preview exposed, `expected_hash_verified_against_source_hash=false`, `source_hash_validated=false`, `revision_id_validated=false`, `available_time_validated=false`, `pit_admissibility_validated=false`, `source_reliability_scored=false`, `reviewer_authority_validated=false`, `target_file_opened_for_expected_hash_verification=false`, `local_file_byte_hash_recomputed=false`, `csv_header_read=false`, `csv_row_count_computed=false`, `csv_values_read=false`, `csv_full_content_read=false`, `real_csv_consumed=false`, and downstream/replay/buy-review/trading/data-write flags false.
- `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification-index`: 1 artifact discovered, latest run id `e020ed1246dd`, `NO_EXPECTED_HASH_VERIFICATION_INPUT`, `PASS`, no expected or actual hash preview, no target CSV opening, no source byte-hash metadata reread for comparison, no hash recomputation, and no real package candidate, active input, buy-review, trading, or protected data writes.
- `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification-health`: `PASS`, 1 checked artifact, 0 issues, 0 errors, 0 warnings, and no target CSV opening, source byte-hash metadata reread for comparison, hash recomputation, real package candidate, active input, buy-review, trading, or protected data writes.
- `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification-status`: latest run id `e020ed1246dd`, `NO_EXPECTED_HASH_VERIFICATION_INPUT`, `PASS`, `FILE_TOUCH_NONE`, `CSV_READ_NONE`, `LOCAL_FILE_HASH_NONE`, no verification performed, no expected or actual hash preview, source/revision/available_time/PIT/source-reliability/reviewer validations false, target file opened false, local byte hash recomputed false, CSV read proof fields false, `real_csv_consumed=false`, `active_replay_input=false`, `trading_allowed=false`, `buy_review_allowed=false`, protected data-write flags false, and checkpoint-planning next action.
- `research-status --root <temp>/outputs/reports --output-dir <temp>/dashboard --config <repo>/config/default.yaml`: Expected-Hash Verification context visible from the temporary artifacts and no live trading or broker API invoked. The isolated temporary root had no later paper workflow context, so the final dashboard stage remained `DATA_PREPARATION_READY`; focused dashboard tests cover preservation of later `PAPER_WORKFLOW_READY` priority.

## Known Limitations

- Expected-hash verification is metadata comparison only.
- It depends on an existing Local File Byte-Hash-Only metadata value.
- It does not prove source reliability, PIT admissibility, reviewer authority, or semantic data validity.
- Full hashes are not Project Source material.
- Non-core surfaces expose preview only.
- Mismatch is `WARN` / actionable context only.
- Views, status, CLI status, and research-status do not recompute hashes, reopen target CSV, reread source byte-hash metadata for comparison, or reverify expected_hash.
- No real package candidate, active reviewed input candidate, real replay input, active replay input, replay evidence bundle, replay decision, replay decision freeze, forward label, future-label join, training dataset, metric computation, signal_score input, model training, active weight, active threshold, stock_profile validation, paper validation, real buy-review, performance validation, or trading workflow is implemented by this checkpoint.
- ChatGPT Project Source files are not created in Git, and `docs/project_sources/` remains intentionally absent.

## Recommended Next Task

ChatGPT review for manual commit/tag v1.77.0 and ChatGPT-side curated Project Source update planning.
