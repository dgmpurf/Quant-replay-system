# Release Checkpoint v1.78.0

v1.78.0 documents Tiny PIT Real Reviewed LOCAL_CSV Package Candidate CSV Physical Data-Line Count-Only core, artifact views, CLI, research-status integration, and checkpoint context.

## Included Work

- The CSV Physical Data-Line Count-Only core is available through `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only`.
- Artifact views are available through `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only-index`, `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only-health`, and `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only-status`.
- `research-status` exposes the latest CSV Physical Data-Line Count-Only context while preserving `PAPER_WORKFLOW_READY` priority.
- `docs/tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only.md` documents physical-line count semantics and safety boundaries.
- `README.md` and `docs/local_research_dashboard.md` describe the v1.78.0 report-only workflow and research-status visibility.

## Lineage

- Previous checkpoint tag: `v1.77.0` at commit `41b6d59`.
- Post-v1.77.0 commits included before this checkpoint documentation:
  - `14925ad Add CSV physical data-line count-only core report-only`
  - `5b8f6f5 Add CSV physical data-line count-only artifact views report-only`
  - `343b6a3 Add CSV physical data-line count-only CLI report-only`
  - `ac1febb Integrate CSV physical data-line count-only research status report-only`
- v1.78.0 is intended to be created after ChatGPT review and manual commit/tag of this checkpoint documentation package.

## Expected Default / No-Input State

- Runtime status: `NO_CSV_PHYSICAL_DATA_LINE_COUNT_INPUT`
- Health status: `PASS`
- Workflow stage: `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_CSV_PHYSICAL_DATA_LINE_COUNT_ONLY_CORE_CREATED_REPORT_ONLY`
- Report-only: `true`
- Diagnostic-only: `true`
- File touch level: `FILE_TOUCH_NONE`
- CSV read level: `CSV_READ_NONE`
- Local file hash level: `LOCAL_FILE_HASH_NONE`
- Expected-hash verification level: `EXPECTED_HASH_VERIFICATION_NONE`
- CSV physical data-line count level: `CSV_PHYSICAL_DATA_LINE_COUNT_NONE`
- CSV physical data-line count computed: `false`
- CSV physical data-line count: empty
- CSV physical data-line count policy: empty
- Target CSV opened for physical data-line count: `false`
- CSV header read: `false`
- CSV header values recorded: `false`
- CSV values read: `false`
- CSV value fields parsed: `false`
- CSV row values stored: `false`
- CSV full content read: `false`
- CSV full content semantically read: `false`
- Real CSV consumed: `false`
- Local file byte hash computed: `false`
- Local file byte hash recomputed: `false`
- Expected-hash verification performed: `false`
- Expected hash verified against local metadata: `false`
- Expected hash verified against source hash: `false`
- Source hash validated: `false`
- Revision id validated: `false`
- Available time validated: `false`
- PIT admissibility validated: `false`
- Source reliability scored: `false`
- Reviewer authority validated: `false`
- All downstream, replay, buy-review, trading, and protected data-write safety flags remain false.

## Expected Safe Count State

- Runtime status: `CSV_PHYSICAL_DATA_LINE_COUNT_ONLY_REPORT_ONLY`
- Health status: `PASS`
- Workflow stage: `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_CSV_PHYSICAL_DATA_LINE_COUNT_ONLY_CORE_CREATED_REPORT_ONLY`
- File touch level: `CSV_PHYSICAL_DATA_LINE_COUNT_ONLY`
- CSV read level: `CSV_PHYSICAL_DATA_LINE_COUNT_ONLY`
- Local file hash level: `LOCAL_FILE_HASH_NONE`
- Expected-hash verification level: `EXPECTED_HASH_VERIFICATION_NONE`
- CSV physical data-line count level: `CSV_PHYSICAL_DATA_LINE_COUNT_ONLY`
- `csv_physical_data_line_count_computed=true`
- `csv_physical_data_line_count` is an integer.
- `csv_physical_data_line_count_policy=PHYSICAL_NON_HEADER_LINE_COUNT`
- `target_csv_opened_for_physical_data_line_count=true` may appear only in this guarded count mode.
- `csv_header_line_skipped_by_policy=true` when a physical header line exists.
- `csv_header_read=false`
- `csv_header_values_recorded=false`
- `csv_values_read=false`
- `csv_value_fields_parsed=false`
- `csv_row_values_stored=false`
- `csv_full_content_read=false`
- `csv_full_content_semantically_read=false`
- `real_csv_consumed=false`
- `local_file_byte_hash_computed=false`
- `local_file_byte_hash_recomputed=false`
- `expected_hash_verification_performed=false`
- `expected_hash_verified_against_local_metadata=false`
- `expected_hash_verified_against_source_hash=false`
- `source_hash_validated=false`
- `revision_id_validated=false`
- `available_time_validated=false`
- `pit_admissibility_validated=false`
- `source_reliability_scored=false`
- `reviewer_authority_validated=false`
- All downstream, replay, buy-review, trading, and data-write safety flags remain false.

## Expected Zero Data-Line State

- Runtime status: `CSV_PHYSICAL_DATA_LINE_COUNT_WARN_ZERO_DATA_LINES`
- Health status: `WARN`
- Workflow stage: `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_CSV_PHYSICAL_DATA_LINE_COUNT_ONLY_CORE_CREATED_REPORT_ONLY`
- `csv_physical_data_line_count_computed=true`
- `csv_physical_data_line_count=0`
- `csv_physical_data_line_count_policy=PHYSICAL_NON_HEADER_LINE_COUNT`
- `target_csv_opened_for_physical_data_line_count=true`
- Negative proof fields and downstream safety flags remain false.

Zero data lines are `WARN` / context only. They are not package failure from a real package validator and do not create replay, buy-review, or trading behavior.

## Physical Data-Line Count Semantics

CSV Physical Data-Line Count-Only counts newline-delimited physical data lines and excludes the first physical line as the header by explicit policy.

It is not semantic CSV record count. Quoted multiline CSV records are counted by physical lines, not logical CSV records.

Count mode requires a package manifest, prior CSV Structural Header-Only metadata, an allowed root, and explicit `--allow-csv-physical-data-line-count-only`.

Prior header metadata is reused only as proof of the header policy. Header values are not copied or exposed, and header metadata is not schema quality, PIT evidence, source reliability evidence, package acceptance, or replay readiness.

## Safety Boundary

This checkpoint is report-only and diagnostic-only. It is not:

- semantic CSV record count
- quoted multiline CSV record handling
- CSV parser use
- target CSV value reading
- header value exposure
- row snippet exposure
- full CSV content semantic reading
- real CSV consumption as package or replay input
- CSV/data reference following beyond the guarded manifest target needed for physical line scan
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

`research-status` exposes CSV Physical Data-Line Count-Only workflow context only. It may expose count and policy fields, negative proof fields, and safety flags, but it must not expose header values, row values, snippets, parsed fields, full-content samples, source hash values, expected hash values, local byte hash values, or target CSV text.

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

- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_views.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_cli.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_local_research_dashboard.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only.py tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_views.py tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_cli.py tests/test_local_research_dashboard.py -q`
- `.venv\Scripts\python.exe -m pytest -m "not slow" -q`

Required CLI validation:

- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only`
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only-index`
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only-health`
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only-status`
- `research-status --root <temp_reports_root> --output-dir <temp_dashboard_root> --config <repo>/config/default.yaml`

Observed validation evidence for this documentation package:

- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only.py`: 55 passed.
- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_views.py`: 15 passed.
- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_cli.py`: 10 passed.
- `tests/test_local_research_dashboard.py`: 338 passed.
- Combined focused suite: 418 passed.
- Full non-slow suite: 5761 passed, 109 deselected, 5 warnings.

Observed CLI evidence from a temporary working directory:

- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only`: run id `e1d3aaf3c2c8`, `NO_CSV_PHYSICAL_DATA_LINE_COUNT_INPUT`, `PASS` health, `FILE_TOUCH_NONE`, `CSV_READ_NONE`, `LOCAL_FILE_HASH_NONE`, `EXPECTED_HASH_VERIFICATION_NONE`, `CSV_PHYSICAL_DATA_LINE_COUNT_NONE`, no count computed, target CSV opened false, CSV header/value/full-content proof fields false, source/revision/available_time/PIT/source-reliability/reviewer validations false, local byte hash recomputation false, expected-hash verification false, `real_csv_consumed=false`, and downstream/replay/buy-review/trading/data-write flags false.
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only-index`: 1 artifact discovered, latest run id `e1d3aaf3c2c8`, `NO_CSV_PHYSICAL_DATA_LINE_COUNT_INPUT`, `PASS`, no count policy, no target CSV opening, and no package candidate, active input, buy-review, trading, or protected data writes.
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only-health`: `PASS`, 1 checked artifact, 0 issues, 0 errors, 0 warnings, no recounting by health, and no package candidate, active input, buy-review, trading, or protected data writes.
- `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only-status`: latest run id `e1d3aaf3c2c8`, `NO_CSV_PHYSICAL_DATA_LINE_COUNT_INPUT`, `PASS`, `FILE_TOUCH_NONE`, `CSV_READ_NONE`, `LOCAL_FILE_HASH_NONE`, `EXPECTED_HASH_VERIFICATION_NONE`, `CSV_PHYSICAL_DATA_LINE_COUNT_NONE`, target CSV opened false, CSV header/value/full-content proof fields false, `real_csv_consumed=false`, validation proof fields false, downstream/replay/buy-review/trading/data-write flags false, and checkpoint-planning next action.
- `research-status --root <temp>/outputs/reports --output-dir <temp>/dashboard --config <repo>/config/default.yaml`: CSV Physical Data-Line Count-Only context visible from temporary status artifacts, latest run id `e1d3aaf3c2c8`, `NO_CSV_PHYSICAL_DATA_LINE_COUNT_INPUT`, `PASS`, negative proof fields false, safety flags false, and no live trading or broker API invoked. The isolated temporary root had no later paper workflow context, so final dashboard stage remained `DATA_PREPARATION_READY`; focused dashboard tests cover preservation of later `PAPER_WORKFLOW_READY` priority.

## Known Limitations

- Physical data-line count is not semantic CSV record count.
- The first physical line is excluded as the header by policy.
- Quoted multiline records are counted by physical lines, not logical CSV records.
- Count mode may open the target CSV in streaming mode only to count physical lines under manifest/root/allow guards.
- `target_csv_opened_for_physical_data_line_count=true` does not mean CSV values were read, fields were parsed, full content was semantically read, `real_csv_consumed` became true, PIT was validated, package readiness was established, replay readiness was established, buy-review was enabled, or trading was authorized.
- No header values, row values, row snippets, parsed fields, full-content samples, source hash values, expected hash values, local byte hash values, or target CSV text are exposed by research-status.
- No real package candidate, active reviewed input candidate, real replay input, active replay input, replay evidence bundle, replay decision, replay decision freeze, forward label, future-label join, training dataset, metric computation, signal_score input, model training, active weight, active threshold, stock_profile validation, paper validation, real buy-review, performance validation, or trading workflow is implemented by this checkpoint.
- ChatGPT Project Source files are not created in Git, and `docs/project_sources/` remains intentionally absent.

## Recommended Next Task

ChatGPT review for manual commit/tag v1.78.0 and ChatGPT-side curated Project Source update planning.
