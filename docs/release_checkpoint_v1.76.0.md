# Release Checkpoint v1.76.0

v1.76.0 documents Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Local File Byte-Hash-Only core, artifact views, CLI, research-status integration, and checkpoint context.

## Included Work

- The Local File Byte-Hash-Only core is available through `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only`.
- Artifact views are available through `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only-index`, `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only-health`, and `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only-status`.
- `research-status` exposes the latest Local File Byte-Hash-Only context while preserving `PAPER_WORKFLOW_READY` priority.
- `docs/tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only.md` documents hash-only semantics and safety boundaries.
- `README.md` and `docs/local_research_dashboard.md` describe the v1.76.0 report-only workflow and research-status visibility.

## Lineage

- Previous checkpoint tag: `v1.75.0` at commit `013ba19`.
- Post-v1.75.0 commits included before this checkpoint documentation:
  - `571d843 Harden CSV structural header-only next action wording report-only`
  - `a515347 Add local file byte-hash-only core report-only`
  - `4067ef6 Add local file byte-hash-only artifact views report-only`
  - `630fc38 Add local file byte-hash-only CLI report-only`
  - `b04157b Integrate local file byte-hash-only research status report-only`
- v1.76.0 is intended to be created after ChatGPT review and manual commit/tag of this checkpoint documentation package.

## Expected Default / No-Input State

- Runtime status: `NO_LOCAL_FILE_BYTE_HASH_INPUT`
- Health status: `PASS`
- Workflow stage: `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_LOCAL_FILE_BYTE_HASH_ONLY_CORE_CREATED_REPORT_ONLY`
- Report-only: `true`
- Diagnostic-only: `true`
- Local file byte hash computed: `false`
- Local file byte hash algorithm: empty
- Local file byte hash preview: empty
- Full SHA-256 recorded in metadata: `false`
- CSV read level: `CSV_READ_NONE`
- CSV header read: `false`
- CSV row count computed: `false`
- CSV row count: empty
- CSV values read: `false`
- CSV full content read: `false`
- Real CSV consumed: `false`
- Source hash validated: `false`
- Revision id validated: `false`
- Available time validated: `false`
- PIT admissibility validated: `false`
- Source reliability scored: `false`
- Reviewer authority validated: `false`
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

## Expected Hash-Only State

- Runtime status: `LOCAL_FILE_BYTE_HASH_ONLY_REPORT_ONLY`
- Health status: `PASS` for safe no-input or hash-only artifacts.
- Workflow stage: `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_LOCAL_FILE_BYTE_HASH_ONLY_CORE_CREATED_REPORT_ONLY`
- `local_file_byte_hash_computed` may be `true`.
- `local_file_byte_hash_algorithm=SHA-256`.
- Full SHA-256 is local core `metadata.json` only.
- Report, index, status, CLI, and research-status expose preview only.
- `csv_read_level=CSV_READ_NONE`.
- `csv_header_read=false`.
- `csv_row_count_computed=false`.
- `csv_row_count=""`.
- `csv_values_read=false`.
- `csv_full_content_read=false`.
- `real_csv_consumed=false`.
- `source_hash_validated=false`.
- `revision_id_validated=false`.
- `available_time_validated=false`.
- `pit_admissibility_validated=false`.
- `source_reliability_scored=false`.
- `reviewer_authority_validated=false`.
- All downstream, replay, buy-review, trading, and data-write safety flags remain false.

## Local File Byte-Hash-Only Semantics

Byte-hash-only means local file identity / integrity metadata only. A manifest-gated, allowed-root-gated, explicit `--allow-local-file-byte-hash-only` run may compute a SHA-256 byte hash and record proof fields. It does not make the CSV admissible, consume the CSV as a package, or create a package candidate.

The workflow does not read CSV headers, count rows, read CSV data values, semantically read full CSV content, follow CSV/data references, verify expected hashes, validate source_hash, validate revision_id, validate real available_time evidence, validate PIT admissibility, score source reliability, validate reviewer authority, or create real package candidates.

## Safety Boundary

This checkpoint is report-only and diagnostic-only. It is not:

- CSV header reading
- row counting
- CSV data value reading
- full CSV content semantic reading
- real CSV consumption as package or replay input
- CSV/data reference following
- expected_hash verification
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

`research-status` exposes the Tiny PIT Local File Byte-Hash-Only workflow as context only. It must not expose the full SHA-256, override later paper workflow priority, or emit or imply `ACTIVE_REPLAY_INPUT_READY`.

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

- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only_views.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only_cli.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_local_research_dashboard.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only.py tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only_views.py tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only_cli.py tests/test_local_research_dashboard.py -q`
- `.venv\Scripts\python.exe -m pytest -m "not slow" -q`

Required CLI validation:

- `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only`
- `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only-index`
- `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only-health`
- `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only-status`
- `research-status --root <temp_reports_root> --output-dir <temp_dashboard_root> --config <repo>/config/default.yaml`

Observed validation evidence for this documentation package:

- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only.py`: 34 passed.
- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only_views.py`: 31 passed.
- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only_cli.py`: 8 passed.
- `tests/test_local_research_dashboard.py`: 329 passed.
- Combined focused suite: 402 passed.
- Full non-slow suite: 5583 passed, 109 deselected, 5 warnings.

Observed CLI evidence from a temporary working directory:

- `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only`: run id `80ac51f0fde8`, `NO_LOCAL_FILE_BYTE_HASH_INPUT`, `PASS` health, `FILE_TOUCH_NONE`, `CSV_READ_NONE`, `LOCAL_FILE_HASH_NONE`, no local file byte hash computed, no algorithm or preview exposed, `csv_header_read=false`, `csv_row_count_computed=false`, `csv_values_read=false`, `csv_full_content_read=false`, `real_csv_consumed=false`, source/revision/available_time/PIT/source-reliability/reviewer validations false, and downstream/replay/buy-review/trading/data-write flags false.
- `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only-index`: 1 artifact discovered, latest run id `80ac51f0fde8`, `NO_LOCAL_FILE_BYTE_HASH_INPUT`, `PASS`, and no hash recomputation or target CSV opening.
- `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only-health`: `PASS`, 1 checked artifact, 0 issues, 0 errors, 0 warnings, and no hash recomputation or target CSV opening.
- `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only-status`: latest run id `80ac51f0fde8`, `NO_LOCAL_FILE_BYTE_HASH_INPUT`, `PASS`, `FILE_TOUCH_NONE`, `CSV_READ_NONE`, `LOCAL_FILE_HASH_NONE`, `real_csv_consumed=false`, `active_replay_input=false`, `trading_allowed=false`, and checkpoint-planning next action.
- `research-status --root <temp>/outputs/reports --output-dir <temp>/dashboard --config <repo>/config/default.yaml`: Local File Byte-Hash-Only context visible, latest run id `80ac51f0fde8`, runtime status `NO_LOCAL_FILE_BYTE_HASH_INPUT`, health `PASS`, workflow stage `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_LOCAL_FILE_BYTE_HASH_ONLY_CORE_CREATED_REPORT_ONLY`, `FILE_TOUCH_NONE`, `CSV_READ_NONE`, `LOCAL_FILE_HASH_NONE`, `hash_computed=false`, no hash preview, and checkpoint-planning next action. The isolated temporary root had no later paper workflow context, so the final dashboard stage remained the earlier local-data stage; focused dashboard tests cover preservation of later `PAPER_WORKFLOW_READY` priority.

## Known Limitations

- Byte-hash-only mode is limited to local file identity / integrity metadata.
- Byte hash proves file bytes, not source reliability, PIT admissibility, reviewer authority, or semantic data validity.
- Full SHA-256 is local core metadata only and is not Project Source material.
- Non-core surfaces expose preview only.
- No expected_hash verification is performed.
- No source_hash validation is performed.
- No revision_id validation is performed.
- No real available_time, source reliability, or reviewer authority logic is proven.
- No real package candidate, active reviewed input candidate, real replay input, active replay input, replay evidence bundle, replay decision, replay decision freeze, forward label, future-label join, training dataset, metric computation, signal_score input, model training, active weight, active threshold, stock_profile validation, paper validation, real buy-review, performance validation, or trading workflow is implemented by this checkpoint.
- ChatGPT Project Source files are not created in Git, and `docs/project_sources/` remains intentionally absent.

## Recommended Next Task

ChatGPT review for manual commit/tag v1.76.0 and ChatGPT-side curated Project Source update planning.
