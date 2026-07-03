# Release Checkpoint v1.79.0

v1.79.0 documents Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Source Hash Revision Available-Time core, artifact views, CLI, research-status integration, and checkpoint context.

## Included Work

- The Source Hash / Revision ID / Available-Time core is available through `tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time`.
- Artifact views are available through `tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time-index`, `tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time-health`, and `tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time-status`.
- `research-status` exposes the latest Source Hash / Revision ID / Available-Time context while preserving `PAPER_WORKFLOW_READY` priority.
- `docs/tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time.md` documents metadata-present, parseability, disclosure, and safety boundaries.
- `README.md` and `docs/local_research_dashboard.md` describe the v1.79.0 report-only workflow and research-status visibility.

## Lineage

- Previous checkpoint tag: `v1.78.0` at commit `6434e35`.
- Post-v1.78.0 commits included before this checkpoint documentation:
  - `4320c31 Add source hash revision available-time core report-only`
  - `34db479 Add source hash revision available-time artifact views report-only`
  - `2b21791 Add source hash revision available-time CLI report-only`
  - `572c65d Integrate source hash revision available-time research status report-only`
- v1.79.0 is intended to be created after ChatGPT review and manual commit/tag of this checkpoint documentation package.

## Expected Default / No-Input State

- Runtime status: `NO_SOURCE_REVISION_TIME_INPUT`
- Health status: `PASS`
- Workflow stage: `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_SOURCE_HASH_REVISION_AVAILABLE_TIME_CORE_CREATED_REPORT_ONLY`
- Report-only: `true`
- Diagnostic-only: `true`
- Source hash validation level: `SOURCE_HASH_VALIDATION_NONE`
- Revision id validation level: `REVISION_ID_VALIDATION_NONE`
- Available-time validation level: `AVAILABLE_TIME_VALIDATION_NONE`
- PIT admissibility level: `PIT_ADMISSIBILITY_NONE`
- Source hash metadata present: `false`
- Source hash format checked: `false`
- Source hash algorithm supported: `false`
- Source hash preview: empty
- Revision id metadata present: `false`
- Revision id type supported: `false`
- Revision consistency checked: `false`
- Available-time metadata present: `false`
- Available-time parseable: `false`
- Available-time timezone present: `false`
- Available-time compared to decision time: `false`
- All source/revision/time validation, PIT, reviewer, replay, buy-review, trading, and protected data-write safety flags remain false.

## Expected Metadata-Present State

- Runtime status: `SOURCE_REVISION_TIME_METADATA_PRESENT_REPORT_ONLY`
- Health status: `PASS`
- Workflow stage: `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_SOURCE_HASH_REVISION_AVAILABLE_TIME_CORE_CREATED_REPORT_ONLY`
- Source hash validation level: `SOURCE_HASH_METADATA_PRESENT_ONLY`
- Revision id validation level: `REVISION_ID_METADATA_PRESENT_ONLY`
- Available-time validation level: `AVAILABLE_TIME_METADATA_PRESENT_ONLY`
- PIT admissibility level: `PIT_ADMISSIBILITY_NONE`
- Source hash metadata present: `true`
- Source hash format checked: `true`
- Source hash algorithm supported: `true`
- Source hash algorithm: `SHA-256`
- Source hash preview may be present, but full source hash must not be public.
- Revision id metadata present: `true`
- Revision id type supported: `true`
- Revision id value recorded: `true`
- Revision consistency checked: `false`
- Available-time metadata present: `true`
- Available-time parseable: `true`
- Available-time timezone present may be true, or a timezone warning may be emitted.
- Available-time compared to decision time: `false`
- Source hash recomputed: `false`
- Source artifact opened: `false`
- Source content read: `false`
- Local file hash recomputed: `false`
- Expected hash reverified: `false`
- Target CSV opened: `false`
- Real CSV consumed: `false`
- Source hash validated: `false`
- Revision id validated: `false`
- Available time validated: `false`
- PIT admissibility validated: `false`
- Source reliability scored: `false`
- Reviewer authority validated: `false`
- All downstream, replay, buy-review, trading, and data-write safety flags remain false.

## Expected Timezone Warning State

- Runtime status: `SOURCE_REVISION_TIME_WARN_TIMEZONE_ASSUMPTION_REQUIRED`
- Health status: `WARN`
- Workflow stage: `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_SOURCE_HASH_REVISION_AVAILABLE_TIME_CORE_CREATED_REPORT_ONLY`
- Available-time metadata may be present and parseable.
- Available-time timezone present: `false`
- Available-time compared to decision time: `false`
- Available time validated: `false`
- PIT admissibility validated: `false`
- Negative proof fields and downstream safety flags remain false.

Timezone warning is review context only. It is not PIT failure, package rejection, replay readiness, buy-review readiness, or trading readiness.

## Metadata Semantics

Source hash metadata presence and SHA-256 format support are disclosure context only. They are not source hash validation, source integrity proof, source reliability scoring, package admissibility, or replay readiness.

Revision id metadata presence and type support are lineage context only. They are not revision validation, revision consistency proof, package readiness, PIT admissibility, or trading readiness.

Available-time metadata presence and parseability are timing metadata context only. They are not available-time adjudication, `available_time <= replay_decision_time` PIT gating, PIT admissibility, replay readiness, buy-review readiness, or trading readiness.

## Safety Boundary

This checkpoint is report-only and diagnostic-only. It is not:

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

## Research-Status Boundary

`research-status` exposes Source Hash / Revision ID / Available-Time workflow context only. It may expose latest run id, runtime status, health status, workflow stage, artifact/report paths, validation levels, source hash preview, revision id type context, available-time parseability and timezone context, issue/warning counts, negative proof fields, and safety flags.

It must not expose full source hashes, source content, source artifact bytes, target CSV content, row values, full file text, private paths, source reliability scores, reviewer approval, package admissibility, replay readiness, buy-review readiness, or trading readiness.

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

- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time_views.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time_cli.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_local_research_dashboard.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time.py tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time_views.py tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time_cli.py tests/test_local_research_dashboard.py -q`
- `.venv\Scripts\python.exe -m pytest -m "not slow" -q`

Required CLI validation:

- `tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time`
- `tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time-index`
- `tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time-health`
- `tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time-status`
- `research-status --root <temp_reports_root> --output-dir <temp_dashboard_root> --config <repo>/config/default.yaml`

Observed validation evidence for this documentation package:

- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time.py`: 26 passed.
- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time_views.py`: 16 passed.
- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time_cli.py`: 10 passed.
- `tests/test_local_research_dashboard.py`: 343 passed.
- Combined focused suite: 395 passed.
- Full non-slow suite: 5818 passed, 109 deselected, 5 warnings.

Observed CLI evidence from a temporary working directory:

- `tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time`: run id `d240d255af9b`, `NO_SOURCE_REVISION_TIME_INPUT`, `PASS` health, validation levels `SOURCE_HASH_VALIDATION_NONE`, `REVISION_ID_VALIDATION_NONE`, `AVAILABLE_TIME_VALIDATION_NONE`, `PIT_ADMISSIBILITY_NONE`, source hash metadata absent, revision id metadata absent, available-time metadata absent, source artifact opened false, source content read false, target CSV opened false, source/local hash recomputation false, expected-hash reverification false, source/revision/available-time/PIT/source-reliability/reviewer validations false, and downstream/replay/buy-review/trading/data-write flags false.
- `tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time-index`: 1 artifact discovered, latest run id `d240d255af9b`, `NO_SOURCE_REVISION_TIME_INPUT`, `PASS`, empty source hash preview, available-time parseable false, available-time compared to decision time false, and no package candidate, active input, buy-review, trading, or protected data writes.
- `tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time-health`: `PASS`, 1 checked artifact, 0 issues, 0 errors, 0 warnings, no metadata reference reopening, no source artifact opening, no hash recomputation, no available-time decision-time comparison, and no package candidate, active input, buy-review, trading, or protected data writes.
- `tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time-status`: latest run id `d240d255af9b`, `NO_SOURCE_REVISION_TIME_INPUT`, `PASS`, validation levels none, `PIT_ADMISSIBILITY_NONE`, source artifact opened false, source content read false, target CSV opened false, source/local hash recomputation false, expected-hash reverification false, source/revision/available-time/PIT/source-reliability/reviewer validations false, and checkpoint-planning next action.
- `research-status --root <temp>/outputs/reports --output-dir <temp>/dashboard --config <repo>/config/default.yaml`: Source Revision Time context visible from temporary status artifacts, latest run id `d240d255af9b`, `NO_SOURCE_REVISION_TIME_INPUT`, `PASS`, validation levels none, `PIT_ADMISSIBILITY_NONE`, available-time compared to decision time false, source/revision/available-time/PIT validation false, trading false, protected data-write flags false, and no live trading or broker API invoked. The isolated temporary root had no later paper workflow context, so final dashboard stage remained `DATA_PREPARATION_READY`; focused dashboard tests cover preservation of later `PAPER_WORKFLOW_READY` priority.

## Known Limitations

- Metadata-present does not mean validated.
- SHA-256 format support does not prove source integrity.
- Revision id presence does not prove revision lineage.
- Available-time parseability does not prove historical availability.
- Timezone warnings are review context only, not PIT failures.
- No source artifact bytes, source content, target CSV content, or protected data paths are opened.
- No real package candidate, active replay input, replay, labels, training, model, stock_profile, paper validation, buy-review, performance validation, or trading behavior is created.

## Recommended Next Task

ChatGPT review for manual commit/tag v1.79.0 and ChatGPT-side curated Project Source update planning.
