# Release Checkpoint v1.81.0

v1.81.0 documents Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight core, artifact views, CLI, research-status integration, and checkpoint context.

## Included Work

- The Preflight core is available through `tiny-pit-real-reviewed-local-csv-package-candidate-preflight`.
- Artifact views are available through `tiny-pit-real-reviewed-local-csv-package-candidate-preflight-index`, `tiny-pit-real-reviewed-local-csv-package-candidate-preflight-health`, and `tiny-pit-real-reviewed-local-csv-package-candidate-preflight-status`.
- `research-status` exposes the latest Preflight context while preserving `PAPER_WORKFLOW_READY` priority when later paper workflow evidence exists.
- `docs/tiny_pit_real_reviewed_local_csv_package_candidate_preflight.md` documents metadata-reference aggregation, evidence-reference-matrix context, missing-evidence classification, blocker/warning semantics, negative proof fields, and safety boundaries.
- `README.md` and `docs/local_research_dashboard.md` describe the v1.81.0 report-only workflow and research-status visibility.

## Lineage

- Previous checkpoint tag: `v1.80.0` at commit `38e5da0`.
- Post-v1.80.0 commits included before this checkpoint documentation:
  - `31da430 Add real reviewed local CSV package candidate preflight core report-only`
  - `ba3b774 Add real reviewed local CSV package candidate preflight artifact views report-only`
  - `b2d9d86 Add real reviewed local CSV package candidate preflight CLI report-only`
  - `52aac9a Integrate real reviewed local CSV package candidate preflight research status report-only`
- v1.81.0 is intended to be created only after ChatGPT review and manual commit/tag of this checkpoint documentation package.

## Expected Statuses

- Default / no-input runtime status: `NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_INPUT`
- Metadata-context runtime status: `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_METADATA_CONTEXT_REPORT_ONLY`
- WARN runtime statuses:
  - `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_WARN_MISSING_OPTIONAL_EVIDENCE`
  - `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_WARN_UNVALIDATED_SOURCE_HASH`
  - `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_WARN_NO_AVAILABLE_TIME_PIT_GATE`
- FAIL / blocked runtime statuses include missing required metadata, unsafe reference metadata, forbidden downstream, reviewer/quality/limitation blocker, forbidden permission, and unsupported validation claim.
- No-input health status: `PASS`
- Metadata-context health status: `PASS` when strict evidence is complete and safe
- WARN health status: `WARN`
- FAIL / blocked health status: `FAIL`
- Workflow stage: `TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_CORE_CREATED_REPORT_ONLY`

## Required Negative Proof Fields

These fields must remain false unless a separately approved future workflow explicitly changes scope:

- `target_csv_opened=false`
- `source_artifact_opened=false`
- `source_content_read=false`
- `csv_header_read_by_preflight=false`
- `csv_physical_data_line_count_computed_by_preflight=false`
- `source_hash_recomputed=false`
- `local_file_hash_recomputed=false`
- `expected_hash_reverified=false`
- `available_time_compared_to_decision_time=false`
- `source_hash_validated=false`
- `revision_id_validated=false`
- `available_time_validated=false`
- `pit_admissibility_validated=false`
- `reviewer_authority_validated=false`
- `quality_status_validated=false`
- `permission_class_validated=false`
- `source_reliability_scored=false`
- `real_reviewed_csv_package_created=false`
- `real_package_candidate_created=false`
- `active_reviewed_input_candidate_created=false`
- `real_replay_input_created=false`
- `active_replay_input=false`
- `replay_execution_allowed=false`
- `buy_review_allowed=false`
- `trading_allowed=false`
- `data_raw_written=false`
- `data_processed_written=false`
- `data_cache_written=false`

## Research-Status Boundary

`research-status` exposes Preflight workflow context only. It may expose latest run id, runtime status, health status, workflow stage, artifact/report paths, preflight id, declared package id metadata, capability levels, evidence reference counts, missing evidence counts, reference presence booleans, unvalidated capability counts, issue/warning/blocker counts, negative proof fields, safety flags, and recommended next task.

It must not expose full hashes, full reviewer identity, source content, source artifact bytes, target CSV content, header values, row values, full file text, private paths, package approval, package admissibility, replay readiness, buy-review readiness, performance validation, or trading readiness.

The final research-status workflow stage must remain `PAPER_WORKFLOW_READY` when later paper workflow context exists.

## Safety Boundary

This checkpoint is report-only and diagnostic-only. It is not:

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
- available_time PIT gate
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

## Validation

Required validation for this checkpoint:

- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_preflight.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_views.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_cli.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_local_research_dashboard.py -q`
- `.venv\Scripts\python.exe -m pytest tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_preflight.py tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_views.py tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_cli.py tests/test_local_research_dashboard.py -q`
- `.venv\Scripts\python.exe -m pytest -m "not slow" -q`

Required CLI validation from a temporary working directory:

- `tiny-pit-real-reviewed-local-csv-package-candidate-preflight --output-root <tmp_output>`
- `tiny-pit-real-reviewed-local-csv-package-candidate-preflight-index --root <tmp_output>`
- `tiny-pit-real-reviewed-local-csv-package-candidate-preflight-health --root <tmp_output>`
- `tiny-pit-real-reviewed-local-csv-package-candidate-preflight-status --root <tmp_output>`
- `research-status --root <tmp_output> --output-dir <tmp_dashboard> --config <repo>/config/default.yaml`

Observed validation evidence for this documentation package:

- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_preflight.py`: 22 passed.
- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_views.py`: 13 passed.
- `tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_preflight_cli.py`: 10 passed.
- `tests/test_local_research_dashboard.py`: 354 passed.
- Combined focused suite: 399 passed.
- Full non-slow suite: 5921 passed, 109 deselected, 5 warnings.
- CLI smoke from a temporary working directory: core/index/health/status/research-status commands exited 0. A controlled status-output smoke confirmed `NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_INPUT`, `PASS`, `PREFLIGHT_NONE`, `PACKAGE_CREATION_NONE`, `CSV_READ_NONE`, `real_package_candidate_created=false`, `active_replay_input=false`, `buy_review_allowed=false`, and `trading_allowed=false`; `research-status` exposed the temporary Preflight context with the same safe no-input boundaries.
- Protected tracked scan: `data/processed/.gitkeep`, `data/raw/.gitkeep`, and `outputs/reports/.gitkeep` only.
- `docs/project_sources` scan: no output.

## Known Limitations

- Metadata-context completeness does not mean validated.
- Required reference presence does not prove package admissibility.
- WARN missing optional evidence is review context only.
- FAIL/blocker states are local actionable context only, not real validator package rejection.
- Source hash, revision id, available time, PIT, reviewer authority, quality, permission, and source reliability are not validated by this workflow.
- No source artifact bytes, source content, target CSV content, header values, row values, or protected data paths are opened.
- No real package candidate, active replay input, replay, labels, training, model, stock_profile, paper validation, buy-review, performance validation, or trading behavior is created.

## Tag Plan

Create tag `v1.81.0` only after ChatGPT review and manual commit/tag. This task does not run `git add`, `git commit`, `git push`, or `git tag`.

## Source Update Note

After v1.81.0 is committed and tagged, prepare a ChatGPT-side external curated Project Source update. Do not create `docs/project_sources`, `SOURCE_UPDATE_NOTES_v1_81_0.md`, or a Project Source package in this checkpoint docs task.

## Recommended Next Task

After checkpoint review and manual commit/tag, the next task should be `Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Post-v1.81 Governance Audit / Next Decision Planning Report-Only v0.1`.
