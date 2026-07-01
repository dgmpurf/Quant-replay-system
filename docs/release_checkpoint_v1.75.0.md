# Release Checkpoint v1.75.0

v1.75.0 documents Tiny PIT Real Reviewed LOCAL_CSV Package Candidate CSV Structural Header-Only core, artifact views, CLI, research-status integration, and checkpoint context.

## Included Work

- The CSV Structural Header-Only core is available through `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only`.
- Artifact views are available through `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only-index`, `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only-health`, and `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only-status`.
- `research-status` exposes the latest CSV Structural Header-Only context while preserving `PAPER_WORKFLOW_READY` priority.
- `docs/tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_header_only.md` documents header-only semantics and safety boundaries.
- `README.md` and `docs/local_research_dashboard.md` describe the v1.75.0 report-only workflow and research-status visibility.

## Lineage

- Previous checkpoint tag: `v1.74.0` at commit `1f5d5df`.
- Post-v1.74.0 commits included before this checkpoint documentation:
  - `c8f0ab6 Harden metadata reference following next-action wording report-only`
  - `f4b70c1 Add CSV structural header-only core report-only`
  - `a15e6bd Add CSV structural header-only artifact views report-only`
  - `1561451 Add CSV structural header-only CLI report-only`
  - `b3270a4 Integrate CSV structural header-only research status report-only`
- v1.75.0 is intended to be created after ChatGPT review and manual commit/tag of this checkpoint documentation package.

## Expected Default / No-Input State

- Runtime status: `NO_CSV_STRUCTURAL_FILE_TOUCH_INPUT`
- Health status: `PASS`
- Workflow stage: `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_CSV_STRUCTURAL_HEADER_ONLY_CORE_CREATED_REPORT_ONLY`
- Report-only: `true`
- Diagnostic-only: `true`
- CSV header read: `false`
- CSV row count computed: `false`
- CSV row count: empty
- CSV values read: `false`
- CSV full content read: `false`
- Local file byte hash computed: `false`
- Local file byte hash algorithm: empty
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

## Expected Header-Only State

- Runtime status: `CSV_STRUCTURAL_HEADER_ONLY_REPORT_ONLY`
- Health status: `PASS` for safe no-input or header-only artifacts.
- Workflow stage: `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_CSV_STRUCTURAL_HEADER_ONLY_CORE_CREATED_REPORT_ONLY`
- `csv_header_read` may be `true`.
- `csv_header_column_count` may be recorded.
- `csv_row_count_computed=false`.
- `csv_row_count=""`.
- `csv_values_read=false`.
- `csv_full_content_read=false`.
- `local_file_byte_hash_computed=false`.
- `local_file_byte_hash_algorithm=""`.
- `real_csv_consumed=false`.
- All downstream, replay, buy-review, trading, and data-write safety flags remain false.

## CSV Structural Header-Only Semantics

Header-only means structural metadata only. A manifest-gated, allowed-root-gated, explicit `--allow-csv-header-only` run may read only the CSV header and record header proof fields. It does not make the CSV admissible, consume the CSV as a package, or create a package candidate.

The workflow does not count rows, read CSV data values, read full CSV content, compute local file byte hashes, follow CSV/data references, validate real source availability, validate real available_time evidence, score source reliability, validate reviewer authority, or create real package candidates.

## Safety Boundary

This checkpoint is report-only and diagnostic-only. It is not:

- row counting
- CSV data value reading
- full CSV content reading
- local file byte hash computation
- real CSV consumption as package or replay input
- CSV/data reference following
- real available_time adjudication
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

`research-status` exposes the Tiny PIT CSV Structural Header-Only workflow as context only. It must not override later paper workflow priority and must not emit or imply `ACTIVE_REPLAY_INPUT_READY`.

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

- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch_views.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch_cli.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_local_research_dashboard.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch.py tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch_views.py tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch_cli.py tests/test_local_research_dashboard.py -q`
- `.venv\Scripts\python.exe -m pytest -m "not slow" -q`

Required CLI validation:

- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only`
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only-index`
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only-health`
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only-status`
- `research-status --root outputs/reports`

Observed validation evidence for this documentation package:

- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch.py`: 24 passed.
- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch_views.py`: 17 passed.
- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch_cli.py`: 6 passed.
- `tests/test_local_research_dashboard.py`: 326 passed.
- Combined focused suite: 373 passed.
- Full non-slow suite: 5507 passed, 109 deselected, 5 warnings.

Observed CLI evidence from a temporary working directory:

- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only`: run id `8efc7e94e340`, `NO_CSV_STRUCTURAL_FILE_TOUCH_INPUT`, `PASS` health, `FILE_TOUCH_NONE`, `CSV_READ_NONE`, `LOCAL_FILE_HASH_NONE`, `csv_header_read=false`, `csv_row_count_computed=false`, no local file byte hash computed, `real_csv_consumed=false`, and all downstream safety flags false.
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only-index`: 1 artifact discovered, latest run id `8efc7e94e340`.
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only-health`: `PASS`, 0 issues, 0 errors, 0 warnings.
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only-status`: latest run id `8efc7e94e340`, `NO_CSV_STRUCTURAL_FILE_TOUCH_INPUT`, `PASS`, `FILE_TOUCH_NONE`, `CSV_READ_NONE`, `LOCAL_FILE_HASH_NONE`, `real_csv_consumed=false`, `active_replay_input=false`, and `trading_allowed=false`.
- `research-status --root <temp>/outputs/reports --output-dir <temp>/dashboard --config <repo>/config/default.yaml`: CSV Structural Header-Only context visible, latest run id `8efc7e94e340`, runtime status `NO_CSV_STRUCTURAL_FILE_TOUCH_INPUT`, health `PASS`, workflow stage `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_CSV_STRUCTURAL_HEADER_ONLY_CORE_CREATED_REPORT_ONLY`, `FILE_TOUCH_NONE`, `CSV_READ_NONE`, `LOCAL_FILE_HASH_NONE`, `real_csv_consumed=false`, `active_replay_input=false`, and `trading_allowed=false`.

## Known Limitations

- Header-only mode is limited to structural metadata.
- Header names are not PIT evidence and do not prove source reliability.
- Header column count is not row count.
- No CSV data values or full content are inspected.
- No local file byte hash is computed.
- No real available_time, source reliability, or reviewer authority logic is proven.
- No real package candidate, active reviewed input candidate, real replay input, active replay input, replay evidence bundle, replay decision, replay decision freeze, forward label, future-label join, training dataset, metric computation, signal_score input, model training, active weight, active threshold, stock_profile validation, paper validation, real buy-review, performance validation, or trading workflow is implemented by this checkpoint.
- ChatGPT Project Source files are not created in Git, and `docs/project_sources/` remains intentionally absent.

## Recommended Next Task

ChatGPT review for manual commit/tag v1.75.0 and ChatGPT-side curated Project Source update planning.
