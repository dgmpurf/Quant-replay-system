# quant-replay-system

A point-in-time historical replay quant research system for China A-share ETFs and stocks.

## Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Source Hash Revision Available-Time v1.79.0

`NO_SOURCE_REVISION_TIME_INPUT`, `SOURCE_REVISION_TIME_METADATA_PRESENT_REPORT_ONLY`, and `SOURCE_REVISION_TIME_WARN_TIMEZONE_ASSUMPTION_REQUIRED` mean Tiny PIT Source Hash / Revision ID / Available-Time artifacts exist as report-only / diagnostic-only source lineage metadata context. This workflow confirms metadata presence, shape, parseability, and disclosure only for `source_hash`, `revision_id`, and `available_time`.

Use `tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time`, `tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time-index`, `tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time-health`, and `tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time-status` to create, discover, safety-check, and summarize the report-only metadata artifacts. `research-status` exposes the latest context while preserving later `PAPER_WORKFLOW_READY` priority.

Source hash disclosure is preview-only on report, index, status, CLI, and research-status surfaces. A timezone assumption is `WARN` / review context only, not PIT failure.

The workflow does not validate `source_hash`, validate `revision_id`, validate or adjudicate `available_time`, compare `available_time <= replay_decision_time`, validate PIT admissibility, open source artifact bytes, read source content, open target CSV files, recompute source or local file hashes, reverify `expected_hash`, score source reliability, validate reviewer authority, create real package candidates, create active replay input, run replay, create labels, train models, create stock_profile or paper validation, create buy-review eligibility, or authorize trading.

## Tiny PIT Real Reviewed LOCAL_CSV Package Candidate CSV Physical Data-Line Count-Only v1.78.0

`NO_CSV_PHYSICAL_DATA_LINE_COUNT_INPUT`, `CSV_PHYSICAL_DATA_LINE_COUNT_ONLY_REPORT_ONLY`, and `CSV_PHYSICAL_DATA_LINE_COUNT_WARN_ZERO_DATA_LINES` mean Tiny PIT CSV Physical Data-Line Count-Only artifacts exist as report-only / diagnostic-only physical non-header line count context. Count mode requires a package manifest, prior CSV Structural Header-Only metadata, an allowed root, and explicit `--allow-csv-physical-data-line-count-only`.

Use `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only`, `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only-index`, `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only-health`, and `tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only-status` to create, discover, safety-check, and summarize the physical data-line count-only report artifacts. `research-status` exposes the latest context while preserving later `PAPER_WORKFLOW_READY` priority.

Physical data-line count means newline-delimited physical data lines only: the first physical line is excluded as the header by explicit policy. It is not semantic CSV record count, and quoted multiline CSV records are not handled as one semantic record. Safe no-input artifacts are `NO_CSV_PHYSICAL_DATA_LINE_COUNT_INPUT` / `PASS`; safe count artifacts are `CSV_PHYSICAL_DATA_LINE_COUNT_ONLY_REPORT_ONLY` / `PASS`; zero data-line artifacts are `CSV_PHYSICAL_DATA_LINE_COUNT_WARN_ZERO_DATA_LINES` / `WARN`.

`target_csv_opened_for_physical_data_line_count=true` may appear only for safe count-mode artifacts and means streaming physical-line scan under manifest/root/allow guards. It does not mean values read, fields parsed, full-content semantic read, `real_csv_consumed`, PIT validation, package readiness, replay readiness, buy-review, or trading.

The workflow does not parse CSV fields, expose header values, row values, row snippets, parsed fields, or full-content samples; compute or recompute hashes; verify expected_hash; validate source_hash, revision_id, available_time, PIT admissibility, source reliability, or reviewer authority; create package candidates, active replay input, replay, labels, training, model, stock_profile, paper validation, buy-review, or trading.

## Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Expected-Hash Verification v1.77.0

`NO_EXPECTED_HASH_VERIFICATION_INPUT`, `EXPECTED_HASH_VERIFICATION_MATCHED_REPORT_ONLY`, and `EXPECTED_HASH_VERIFICATION_MISMATCHED_REPORT_ONLY` mean Tiny PIT Expected-Hash Verification artifacts exist as report-only / diagnostic-only metadata comparison context. Expected-hash verification compares a manifest-declared expected SHA-256 with an existing Local File Byte-Hash-Only metadata value only. Verification mode requires an expected-hash manifest, a local byte-hash metadata path, an allowed root, and explicit `--allow-expected-hash-verification`.

Use `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification`, `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification-index`, `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification-health`, and `tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification-status` to create, discover, safety-check, and summarize the expected-hash report-only artifacts. `research-status` exposes the latest Expected-Hash Verification context while preserving later `PAPER_WORKFLOW_READY` priority.

Matched artifacts are `PASS`. Mismatched artifacts are `WARN` with `actionable_mismatch=true`; mismatch is not a crash, not package approval, not package rejection from a real package validator, not a source_hash failure, not a PIT failure, and not reviewer authority failure. Full expected hashes and full actual local hashes are not exposed outside the allowed local metadata policy; report, index, status, CLI, and research-status expose preview-only fields.

The workflow does not open target CSV files, recompute hashes, read CSV headers, count rows, read CSV data values, semantically read full CSV content, consume CSV as package or replay input, validate source_hash, validate revision_id, validate available_time, validate PIT admissibility, score source reliability, validate reviewer authority, create real package candidates, create active replay input, run replay, create labels, train models, create stock_profile or paper validation, create buy-review eligibility, or authorize trading.

## Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Local File Byte-Hash-Only v1.76.0

`NO_LOCAL_FILE_BYTE_HASH_INPUT` and `LOCAL_FILE_BYTE_HASH_ONLY_REPORT_ONLY` mean Tiny PIT Local File Byte-Hash-Only artifacts exist as report-only / diagnostic-only governance context. Byte-hash-only means local file identity / integrity metadata only: the core hash mode requires a manifest, an allowed root, and explicit `--allow-local-file-byte-hash-only`; SHA-256 is fixed for v0.1.

Use `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only`, `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only-index`, `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only-health`, and `tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only-status` to create, discover, safety-check, and summarize the byte-hash-only report-only artifacts. `research-status` exposes the latest Local File Byte-Hash-Only context while preserving later `PAPER_WORKFLOW_READY` priority.

Full SHA-256 is local core `metadata.json` only; report, index, status, CLI, and research-status expose preview only. The workflow does not read CSV headers, count rows, read CSV data values, semantically read full CSV content, consume CSV as package or replay input, validate source_hash, validate revision_id, validate available_time, validate PIT admissibility, score source reliability, validate reviewer authority, create real package candidates, create active replay input, run replay, create labels, train models, create stock_profile or paper validation, create buy-review eligibility, or authorize trading.

## Tiny PIT Real Reviewed LOCAL_CSV Package Candidate CSV Structural Header-Only v1.75.0

`NO_CSV_STRUCTURAL_FILE_TOUCH_INPUT` and `CSV_STRUCTURAL_HEADER_ONLY_REPORT_ONLY` mean Tiny PIT CSV Structural Header-Only artifacts exist as report-only / diagnostic-only governance context. Header-only means structural metadata only: a manifest-gated, allowed-root-gated, explicit `--allow-csv-header-only` run may read only the CSV header and record header proof fields.

Use `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only`, `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only-index`, `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only-health`, and `tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only-status` to create, discover, safety-check, and summarize the header-only report-only artifacts. `research-status` exposes the latest CSV Structural Header-Only context while preserving later `PAPER_WORKFLOW_READY` priority.

The workflow does not count rows, read CSV data values, read full CSV content, compute byte hashes, consume CSV as package or replay input, create real package candidates, validate PIT admissibility, create active replay input, run replay, create labels, train models, create stock_profile or paper validation, create buy-review eligibility, or authorize trading.

## Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Metadata-Reference-Following v1.74.0

`NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_INPUT`, `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCES_DECLARED_REPORT_ONLY`, and `REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCES_FOLLOWED_REPORT_ONLY` mean Tiny PIT metadata-reference-following artifacts exist as report-only / diagnostic-only governance context. `references_followed=true` means only whitelisted local JSON metadata references were followed under explicit allowed roots. It does not mean CSV files, data references, raw document bodies, external sources, package directories, or real reviewed package candidates were followed.

Use `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following`, `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following-index`, `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following-health`, and `tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following-status` to create, discover, safety-check, and summarize the metadata-reference-following report-only artifacts. `research-status` exposes the latest metadata-reference-following context while preserving later `PAPER_WORKFLOW_READY` priority.

The workflow preserves the hard `CSV_READ_NONE` boundary. It does not consume real CSVs, read CSV headers or rows, compute local byte hashes, follow CSV/data references, validate real available_time/source/reviewer evidence, create real reviewed CSV packages, create real package candidates, create active reviewed input, create real or active replay input, emit `ACTIVE_REPLAY_INPUT_READY`, run replay, create labels, join future labels, train models, create active weights or thresholds, validate stock_profile, validate paper workflow, create buy-review eligibility, set buy_review_allowed, validate strategy performance, run current-candidates, build snapshots, mutate signal_semantics, call broker/order/message/API/trading systems, or write data/raw, data/processed, or data/cache.

## Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Manifest-Only Preflight Prototype v1.73.0

`REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_PROTOTYPE_NO_INPUT` means manifest-only / metadata-only Tiny PIT real reviewed LOCAL_CSV package candidate preflight prototype artifacts exist for future governance context only. The checkpoint is not a real reviewed CSV package, not a real package candidate, not a real PIT validator, not active reviewed input, not real replay input, not active replay input, not `ACTIVE_REPLAY_INPUT_READY`, not replay execution, not replay evidence bundles, not replay decisions, not replay decision freezes, not forward labels, not future-label joins, not training datasets, not metric computation, not signal_score inputs, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

Use `tiny-pit-real-reviewed-local-csv-package-candidate-real-preflight-prototype`, `tiny-pit-real-reviewed-local-csv-package-candidate-real-preflight-prototype-index`, `tiny-pit-real-reviewed-local-csv-package-candidate-real-preflight-prototype-health`, and `tiny-pit-real-reviewed-local-csv-package-candidate-real-preflight-prototype-status` to create, discover, safety-check, and summarize the manifest-only prototype. `research-status` exposes the latest prototype context while preserving later `PAPER_WORKFLOW_READY` priority.

## Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Contract Fixture v1.72.0

`REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY` means synthetic/report-only Tiny PIT real reviewed LOCAL_CSV package candidate preflight contract fixture artifacts exist for future preflight governance context only. The checkpoint is not a real reviewed CSV package, not a real package candidate, not an active reviewed input candidate, not real replay input, not active replay input, not `ACTIVE_REPLAY_INPUT_READY`, not replay execution, not replay evidence bundles, not replay decisions, not replay decision freezes, not forward labels, not future-label joins, not training datasets, not metric computation, not signal_score inputs, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

Use `tiny-pit-real-reviewed-local-csv-package-candidate-preflight-contract-fixture`, `tiny-pit-real-reviewed-local-csv-package-candidate-preflight-contract-fixture-index`, `tiny-pit-real-reviewed-local-csv-package-candidate-preflight-contract-fixture-health`, and `tiny-pit-real-reviewed-local-csv-package-candidate-preflight-contract-fixture-status` to create, discover, safety-check, and summarize the synthetic preflight contract fixture. `research-status` exposes the latest fixture context while preserving later `PAPER_WORKFLOW_READY` priority.

## Tiny PIT Real Reviewed Package Candidate Contract Fixture v1.71.0

`REAL_REVIEWED_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY` means synthetic/report-only Tiny PIT real reviewed package candidate contract fixture artifacts exist for future package-candidate governance context only. The checkpoint is not a real reviewed CSV package, not an active reviewed input candidate, not real replay input, not active replay input, not `ACTIVE_REPLAY_INPUT_READY`, not replay execution, not replay evidence bundles, not replay decisions, not replay decision freezes, not forward labels, not future-label joins, not training datasets, not metric computation, not signal_score inputs, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

Use `tiny-pit-real-reviewed-package-candidate-contract-fixture`, `tiny-pit-real-reviewed-package-candidate-contract-fixture-index`, `tiny-pit-real-reviewed-package-candidate-contract-fixture-health`, and `tiny-pit-real-reviewed-package-candidate-contract-fixture-status` to create, discover, safety-check, and summarize the synthetic contract fixture. `research-status` exposes the latest fixture context while preserving later `PAPER_WORKFLOW_READY` priority.

## Tiny PIT Reviewed Package Fixture v1.70.0

`TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY` means synthetic/report-only Tiny PIT reviewed package fixture artifacts exist for diagnostics and future reviewed package governance only. The checkpoint is not a real reviewed CSV package, not an active reviewed input candidate, not real replay input, not active replay input, not `ACTIVE_REPLAY_INPUT_READY`, not replay execution, not replay evidence bundles, not replay decisions, not replay decision freezes, not forward labels, not future-label joins, not training datasets, not metric computation, not signal_score inputs, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, snapshots, signal_semantics mutation, active stock_profile, promoted/production models, active thresholds, advisory predictions/probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes. No trading is authorized.

## Tiny PIT Admissibility Validator v1.69.0

`TINY_PIT_ADMISSIBILITY_VALIDATOR_SYNTHETIC_CORE_CREATED` means synthetic/report-only Tiny PIT validator package cases were evaluated for diagnostics and future PIT admissibility governance only. The checkpoint is not a real PIT validator, not real reviewed CSV packages, not active reviewed input candidates, not real replay inputs, not active replay input, not replay execution, not replay evidence bundles, not replay decisions, not replay decision freezes, not forward labels, not future-label joins, not training datasets, not metric computation, not signal_score inputs, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, snapshots, signal_semantics mutation, active stock_profile, promoted/production models, active thresholds, advisory predictions/probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes. No trading is authorized.

## Tiny PIT Admissibility Validator Contract Fixture v1.68.0

`TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED` means synthetic/report-only Tiny PIT admissibility validator contract fixture rows exist for schema governance only. The checkpoint is not a real PIT validator, not real reviewed CSV packages, not active reviewed input candidates, not real replay inputs, not replay evidence bundles, not replay decisions, not replay decision freezes, not forward labels, not future-label joins, not training datasets, not metric computation, not signal_score inputs, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, snapshots, signal_semantics mutation, active stock_profile, promoted/production models, active thresholds, advisory predictions/probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes. No trading is authorized.

## Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture v1.67.0

`REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED` means synthetic/report-only reviewed LOCAL_CSV replay prototype input contract fixture rows exist for schema governance only. The checkpoint is not real reviewed CSV packages, not active reviewed input candidates, not a PIT admissibility validator, not real replay inputs, not replay evidence bundles, not replay decisions, not replay decision freezes, not forward labels, not future-label joins, not training datasets, not metric computation, not signal_score inputs, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, snapshots, signal_semantics mutation, active stock_profile, promoted/production model, active thresholds, advisory predictions/probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes. Real reviewed CSV packages, PIT admissibility validation, replay inputs, replay evidence bundles, replay decisions, decision freezes, forward labels, training datasets, metric computation, signal_score inputs, model training, stock_profile validation, paper approval, buy-review, performance validation, and trading require separate exact approval.

## Forward Return Label Schema Fixture v1.66.0

`FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED` means synthetic/report-only forward return label fixture rows exist for schema governance only. The checkpoint is not real forward labels, not future labels joined to decision inputs, not signal_score input authorization, not model training input authorization, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, snapshots, signal_semantics mutation, active stock_profile, promoted/production model, active thresholds, advisory predictions/probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes. Real forward labels, future-label joins, signal_score inputs, model training, stock_profile validation, paper approval, buy-review, performance validation, and trading require separate exact approval.

## Replay Decision Schema Fixture v1.65.0

`REPLAY_DECISION_SCHEMA_FIXTURE_CREATED` means synthetic/report-only replay decision fixture rows exist for schema governance only. The checkpoint is not real replay decisions, not real replay evidence bundle consumption, not forward labels, not future labels joined, not signal_score inputs, not model training inputs, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, snapshots, signal_semantics mutation, active stock_profile, promoted/production model, active thresholds, advisory predictions/probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes. Real replay decisions, replay evidence bundle consumption, decision freeze, labels, signal_score inputs, model training, stock_profile validation, paper approval, buy-review, performance validation, and trading require separate exact approval.

## Replay Evidence Bundle Schema Fixture v1.64.0

`REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED` means synthetic/report-only replay evidence bundle fixture rows exist for schema governance only. The checkpoint is not real replay evidence bundles, not replay decisions, not forward labels, not future labels, not production factor observations, not real factor observations, not production factor registry, not active factor library, not production event ingestion, not active event library, not production company exposure mapping, not real raw document ingestion, not signal_score implementation, not authorized signal_score input, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, snapshots, signal_semantics mutation, active stock_profile, promoted/production model, active thresholds, advisory predictions/probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes. Real replay evidence bundles, replay decisions, labels, signal_score inputs, model training, stock_profile validation, paper approval, buy-review, performance validation, and trading require separate exact approval.

## Factor Observation Schema Fixture v1.63.0

`FACTOR_OBSERVATION_SCHEMA_FIXTURE_CREATED` means synthetic/report-only factor observation fixture rows exist for schema governance only. The checkpoint is not real factor observations, not production factor registry, not active factor library, not production event ingestion, not production company exposure mapping, not real raw document ingestion, not replay evidence bundle, not replay decisions, not forward labels, not signal_score implementation, not normalization/winsorization/direction-adjusted runtime, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, snapshots, signal_semantics mutation, active stock_profile, promoted/production model, active thresholds, advisory predictions/probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes. Real factor observations, replay inputs, labels, model training, stock_profile validation, paper approval, buy-review, performance validation, and trading require separate exact approval.

## Event Structured Schema Fixture v1.62.0

`EVENT_STRUCTURED_SCHEMA_FIXTURE_CREATED` means synthetic/report-only event structured fixture rows exist for schema governance only. The checkpoint is not production event ingestion, not active event library, not real raw document ingestion, not real source adapter, not factor observation, not production company exposure mapping, not replay evidence bundle, not signal_score implementation, not model training, not active weights, not active thresholds, not stock_profile validation, not paper validation, not real buy-review eligibility, does not set buy_review_allowed, and is not strategy performance validation.

It does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, and does not authorize broker/order/message/API/trading. Production event ingestion, active event libraries, real source adapters, factor observations, replay evidence bundles, signal_score, model training, stock_profile validation, buy-review, performance validation, and trading require separate exact approval.

The first goal is to build an explainable scoring workflow, replay historical decision dates using only data available at that time, select candidates, simulate T+1 execution, evaluate forward performance, and later calibrate weights, thresholds, and risk rules.

This project is research infrastructure. It is not an automatic trading bot, high-frequency system, broker auto-order system, insider-information system, or profit guarantee.

## MVP v0.1

Included now:

- Python 3.10+ project skeleton.
- Local YAML configuration.
- Local CSV mock data.
- Local CSV ingestion and processed snapshot builder.
- Data quality summary reports for processed replay inputs.
- Snapshot quality gate for full processed snapshot manifests.
- Optional snapshot quality preflight for replay-like workflows.
- Data preparation artifact index and health check for pipeline, quality, snapshot, and current-candidate outputs.
- Data preparation workflow status dashboard for the latest local data-prep stage and next manual action.
- Current/as-of-date candidate generation from local snapshots for paper-trading review.
- Deterministic signal advisory semantics policy for safe advisory label mapping.
- Signal advisory contract and local alert preview artifacts from current-candidates outputs.
- Current candidate artifact index and health check for local candidate run navigation.
- Current-candidate to paper-trading handoff helper for healthy local candidate artifacts.
- Current-candidate to paper-review handoff helper for manual review update templates.
- Placeholder modules for data, scoring, replay, execution, evaluation, calibration, and risk.
- Point-in-time data contract for market data, universe snapshots, and corporate actions.
- Trading calendar and T+1 execution calendar for daily replay.
- Point-in-time-safe technical indicators for timing research.
- Point-in-time factor dataset builder for research features.
- Explainable score engine and candidate selector for ranked research candidates.
- Replay run orchestrator for end-to-end auditable single-date replays.
- Hardened replay report artifacts with markdown, CSV exports, and metadata JSON.
- Batch replay orchestration for multi-date replay runs and aggregate reports.
- Parameter calibration over explicit small grids using batch replay outputs.
- Portfolio simulation with cash, trade, position, and equity ledgers.
- Portfolio-aware batch replay and calibration using account-level metrics.
- Walk-forward validation for train/validation/test parameter checks.
- Manual paper trading journal for reviewed candidates and hypothetical fills.
- Paper trading review workflow for local approve/reject/watch audit decisions.
- Paper trading review template health check before applying edited review updates.
- Daily paper trading runner for local decision logs, fills, and paper reports.
- Paper trading CLI for daily reports, fills validation, and fills templates.
- Paper trading fill reconciliation for decision/fill audit checks before daily reports.
- Paper trading artifact index for local report and CSV navigation.
- Paper trading artifact health check for stale or unreadable local files.
- Paper trading workflow status dashboard for latest stage and next manual action.
- Unified local research workflow dashboard from data preparation through paper trading.
- Baseline pytest setup.

Not included:

- Live broker trading.
- Real market data ingestion.
- Production strategy logic.
- Auto-order placement.

## Quick Start

```powershell
cd "G:\AICODING\Quantitative Trading\quant-replay-system"
python -m pip install -e ".[dev]"
python -m pytest
```

## Development Setup

For a clean Windows CMD setup with a virtual environment, `.env` file, test command, and sample replay command, see [docs/environment_setup.md](docs/environment_setup.md).

For quick, full, E2E, and duration-profiled test commands, see [docs/testing_strategy.md](docs/testing_strategy.md).

For the standard reusable Codex prompt structure for future tasks, see [docs/CODEX_PROMPT_STANDARD.md](docs/CODEX_PROMPT_STANDARD.md).

For the product vision around research, signal advisory, human-confirmed execution assistance, later-stage automation, and later-stage international expansion, see [docs/product_vision.md](docs/product_vision.md).

For the v0.99.0 checkpoint covering current-candidates backfill execution manifest integration into unified `research-status`, see [docs/release_checkpoint_v0.99.0.md](docs/release_checkpoint_v0.99.0.md).

For the v0.98.0 checkpoint covering current-candidates backfill execution manifest index, health, and status views, see [docs/release_checkpoint_v0.98.0.md](docs/release_checkpoint_v0.98.0.md).

For local CSV ingestion, validation, and processed snapshot manifests, see [docs/data_ingestion.md](docs/data_ingestion.md).

For processed data quality summaries before replay, see [docs/data_quality.md](docs/data_quality.md).

For full-snapshot PASS/WARN/FAIL quality gates before replay, see [docs/snapshot_quality_gate.md](docs/snapshot_quality_gate.md).

For optional snapshot quality preflight checks inside replay, batch, calibration, and walk-forward flows, see [docs/snapshot_quality_preflight.md](docs/snapshot_quality_preflight.md).

For CLI flags that enable snapshot preflight on replay-like workflows, see [docs/snapshot_quality_preflight_cli.md](docs/snapshot_quality_preflight_cli.md).

For current/as-of-date candidate generation from local snapshots, see [docs/current_candidate_generation.md](docs/current_candidate_generation.md).

`current-candidates --selection-profile demo` is available for tiny local artifact/workflow validation only. The default selection profile and research thresholds remain unchanged, and demo candidates are marked as not strategy recommendations.

For planning multi-date current-candidates backfills from existing local market-cache coverage without generating candidates, see [docs/current_candidates_backfill_plan.md](docs/current_candidates_backfill_plan.md). `current-candidates-backfill-plan` records feasible signal dates, indicator warmup coverage, and forward-horizon coverage only; it does not mutate cache, run data-pipeline, fetch data, send messages, or place orders.

Use `current-candidates-backfill-plan-index`, `current-candidates-backfill-plan-health`, and `current-candidates-backfill-plan-status` to discover, safety-check, and summarize those plan artifacts before any candidate generation is executed.

For checking whether a reviewed multi-date plan already has point-in-time-valid snapshot inputs before any candidate generation, see [docs/current_candidates_backfill_execution_manifest.md](docs/current_candidates_backfill_execution_manifest.md). `current-candidates-backfill-execution-manifest` is readiness-only: it does not run current-candidates, build snapshots, compute forward labels, mutate cache, send messages, connect to brokers, or place orders.

Use `current-candidates-backfill-execution-manifest-index`, `current-candidates-backfill-execution-manifest-health`, and `current-candidates-backfill-execution-manifest-status` to discover, safety-check, and summarize readiness manifests. Blocked rows identify missing or point-in-time invalid inputs; they are not candidate generation failures and do not imply strategy performance validation.

`research-status` includes the latest `current-candidates-backfill-execution-manifest-status` as execution-readiness context, including linked plan id, ready/blocked counts, blocker counts such as `BLOCKED_UNIVERSE_AS_OF`, health status, and report path. The manifest remains planning-only; later paper workflow priority is preserved. See [docs/local_research_dashboard.md#current-candidates-backfill-execution-manifest-status](docs/local_research_dashboard.md#current-candidates-backfill-execution-manifest-status).

For blocked `BLOCKED_UNIVERSE_AS_OF` rows, use `pit-universe-overlay-plan` to create a manual review template for point-in-time universe overlays; see [docs/point_in_time_universe_overlay_plan.md](docs/point_in_time_universe_overlay_plan.md). The template does not approve a universe, build snapshots, run current-candidates, compute labels, or place orders. Use `pit-universe-overlay-plan-index`, `pit-universe-overlay-plan-health`, and `pit-universe-overlay-plan-status` to discover, safety-check, and summarize those templates.

`research-status` includes the latest `pit-universe-overlay-plan-status` as PIT universe preparation context, including manual-review counts, valid-for-signal-date counts, survivorship-bias warning counts, health status, and report path. `NEEDS_MANUAL_REVIEW` rows are not valid PIT universe rows yet, and later paper workflow priority is preserved. See [docs/local_research_dashboard.md#pit-universe-overlay-plan-status](docs/local_research_dashboard.md#pit-universe-overlay-plan-status).

Use `pit-universe-overlay-review` to apply local reviewer updates to a PIT overlay plan and validate row-level point-in-time evidence; see [docs/point_in_time_universe_overlay_review.md](docs/point_in_time_universe_overlay_review.md). The review workflow writes evidence artifacts only and does not export usable universe data, build snapshots, run current-candidates, compute labels, send messages, or place orders.

Use `pit-universe-overlay-review-index`, `pit-universe-overlay-review-health`, and `pit-universe-overlay-review-status` to discover, safety-check, and summarize reviewed PIT universe approval artifacts. `research-status` includes the latest review as preparation context, including approved rows, unresolved survivorship warnings, and evidence gaps, while preserving later paper workflow priority.

Use `pit-universe-overlay-export-readiness` to check whether reviewed PIT universe rows are complete enough for a later explicit universe export workflow; see [docs/point_in_time_universe_overlay_export_readiness.md](docs/point_in_time_universe_overlay_export_readiness.md). The readiness workflow writes report artifacts only and does not write usable universe files under `data/raw` or `data/processed`.

Use `pit-universe-overlay-export-readiness-index`, `pit-universe-overlay-export-readiness-health`, and `pit-universe-overlay-export-readiness-status` to discover, safety-check, and summarize PIT universe export-readiness artifacts. `research-status` includes the latest export-readiness status as preparation context, including blocked/no-approved-rows state, export-ready count, missing required-column count, unresolved survivorship-warning count, and report path, while preserving later paper workflow priority.

Use `pit-universe-export-staging` to create guarded PIT universe staging previews from export-ready rows under `outputs/reports` only; see [docs/point_in_time_universe_export_staging.md](docs/point_in_time_universe_export_staging.md). The staging workflow blocks diagnostic sources by default and still does not write `data/raw` or `data/processed`, run current-candidates, build snapshots, compute labels, send messages, or place orders.

Use `pit-universe-export-staging-index`, `pit-universe-export-staging-health`, and `pit-universe-export-staging-status` to discover, safety-check, and summarize staging artifacts. `research-status` includes the latest staging context, including no-ready-row blocking, staged row counts, diagnostic-source flags, and report path, while preserving later paper workflow priority.

Use `pit-universe-evidence-completion-helper` to generate a report-only evidence completion template for reviewed PIT universe rows; see [docs/point_in_time_universe_evidence_completion_helper.md](docs/point_in_time_universe_evidence_completion_helper.md). Optional base-universe rows are joined as non-authoritative `suggested_*` hints only. The helper does not approve rows, export universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, compute labels, send messages, or place orders.

Use `pit-universe-evidence-completion-helper-index`, `pit-universe-evidence-completion-helper-health`, and `pit-universe-evidence-completion-helper-status` to discover, safety-check, and summarize evidence helper artifacts. `research-status` includes the latest helper context, including needs-evidence counts, non-authoritative base hints, future-dated hint warnings, and authoritative-hint counts, while preserving later paper workflow priority.

Use `pit-universe-evidence-review-worklist` to convert the active helper and review artifacts into row-level, symbol-level, and date-level reviewer worklists; see [docs/point_in_time_universe_evidence_review_worklist.md](docs/point_in_time_universe_evidence_review_worklist.md). The worklist is template/report-only: it does not approve rows, export universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, compute labels, send messages, or place orders.

Use `pit-universe-evidence-update-ingestion` to validate a reviewer-completed worklist update CSV and produce a clean `pit_universe_review_updates.csv` for later manual `pit-universe-overlay-review`; see [docs/point_in_time_universe_evidence_update_ingestion.md](docs/point_in_time_universe_evidence_update_ingestion.md). The validator does not apply approvals, rerun review, export universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, compute labels, send messages, or place orders.

Use `pit-universe-evidence-update-ingestion-index`, `pit-universe-evidence-update-ingestion-health`, and `pit-universe-evidence-update-ingestion-status` to discover, safety-check, and summarize evidence update ingestion artifacts. `research-status` includes the latest ingestion context, including ready-for-review-update counts, blocked counts, clean review-updates path, suggested-copy-risk counts, and local-only safety flags, while preserving later paper workflow priority.

Use `pit-evidence-checklist-validator` to compare completed or draft PIT evidence update rows against strict `stock_core` and `etf_core` evidence checklists before any explicit overlay review; see [docs/pit_evidence_checklist_validator.md](docs/pit_evidence_checklist_validator.md). The validator can produce an approval-candidate preview, but it does not apply approval, rerun PIT review, export universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, compute labels, send messages, or place orders.

Use `pit-evidence-checklist-validator-index`, `pit-evidence-checklist-validator-health`, and `pit-evidence-checklist-validator-status` to discover, safety-check, and summarize strict checklist artifacts. `research-status` includes the latest validator context, including checklist-pass and blocked counts by profile, while preserving later paper workflow priority.

Use `pit-official-status-evidence-packet` to consolidate official/public source-access diagnostics, prior evidence discovery, and local EOD cache context into first-batch PIT status evidence packets; see [docs/pit_official_status_evidence_packet.md](docs/pit_official_status_evidence_packet.md). The packet workflow is report-only: it classifies evidence strength, keeps incomplete rows as `NEEDS_MORE_EVIDENCE`, and does not apply approvals, run PIT review, export universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, or compute labels.

Use `pit-official-status-evidence-packet-index`, `pit-official-status-evidence-packet-health`, and `pit-official-status-evidence-packet-status` to discover, safety-check, and summarize packet artifacts. `research-status` includes the latest packet context, including supporting official symbol-level counts, local EOD cache counts, missing evidence counts, checklist-pass counts, and blocked counts while preserving later paper workflow priority.

Use `pit-official-status-evidence-packet-enrichment` to merge official same-date SZSE quotation context and reviewed no-hit policy support into the latest PIT evidence packet; see [docs/pit_official_status_evidence_packet_enrichment.md](docs/pit_official_status_evidence_packet_enrichment.md). The enrichment remains report-only: it does not approve rows, run PIT review, export universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, or compute labels.

Use `one-row-checklist-pass-candidate-preview` to inspect whether one target row has enough reviewed material evidence for a checklist-pass candidate preview; see [docs/one_row_checklist_pass_candidate_preview.md](docs/one_row_checklist_pass_candidate_preview.md). The current preview is report-only/context-only: it does not approve rows, create clean `review_updates.csv`, run PIT review/export/staging/current-candidates, write data files, build snapshots, or compute labels. `research-status` includes the latest preview context while preserving later paper workflow priority.

Use `historical-replay-input-gate-validator-fixture` to create report-only contract cases for a future historical replay input gate validator; see [docs/historical_replay_input_gate_validator_fixture.md](docs/historical_replay_input_gate_validator_fixture.md). Its index, health, and status commands make the fixture visible in `research-status` without implementing the real validator, running real replay, creating active replay input, computing forward labels, training weights, creating active stock profiles, or creating real buy-review eligibility.

Use `historical-replay-input-gate-validator` to run the report-only real validator against a local replay input package; see [docs/historical_replay_input_gate_validator.md](docs/historical_replay_input_gate_validator.md). Its index, health, and status commands are visible in `research-status` and preserve later paper workflow priority. `NO_INPUT` and future pass-candidate states are not active replay input and do not run replay, compute labels, train weights, create stock profiles, or create real buy-review eligibility.

Use `minimal-replay-input-package-fixture-smoke` to create a tiny report-only replay input package fixture and run the report-only validator against it; see [docs/minimal_replay_input_package_fixture_smoke.md](docs/minimal_replay_input_package_fixture_smoke.md). Use `minimal-replay-input-package-fixture-smoke-index`, `minimal-replay-input-package-fixture-smoke-health`, and `minimal-replay-input-package-fixture-smoke-status` to discover, safety-check, and summarize smoke artifacts. The smoke can report `REPLAY_INPUT_GATE_PASS_CANDIDATE` and `SMOKE_PASS_CANDIDATE_READY`, but it is not active replay input and not `ACTIVE_REPLAY_INPUT_READY`: it does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, and does not create real buy-review eligibility.

Use `forward-return-label` to create report-only future outcome label context after replay decisions have been frozen; see [docs/forward_return_label.md](docs/forward_return_label.md). Use `forward-return-label-index`, `forward-return-label-health`, and `forward-return-label-status` to discover, safety-check, and summarize label artifacts. `research-status` includes the latest forward-return label context, including source replay-decision-freeze lineage and safety flags, while preserving later paper workflow priority. This layer is not training, not stock_profile creation, not buy-review eligibility, not paper approval, not performance validation, and not trading.

Use `training-evaluation` to create report-only Training / Evaluation Phase 1 dataset/planning context from frozen replay decisions and forward-return labels; see [docs/training_evaluation.md](docs/training_evaluation.md). Use `training-evaluation-index`, `training-evaluation-health`, and `training-evaluation-status` to discover, safety-check, and summarize those artifacts. The workflow can reach `READY_FOR_TRAINING_EVALUATION_DATASET` without allow and can create `TRAINING_EVALUATION_DATASET_CREATED` report-only dataset/planning artifacts with explicit allow. `TRAINING_EVALUATION_DATASET_CREATED` does not compute metrics, does not create training_result, does not train weights, does not create model_version, does not optimize thresholds, does not create predictions, does not create calibrated probabilities, does not create feature importance, does not create active stock profiles, does not create real buy-review eligibility, does not apply paper approval, does not claim strategy performance validation, and does not authorize trading. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `metric-evaluation` to create report-only Metric / Evaluation Phase 1 structural planning context from Training / Evaluation Phase 1 artifacts; see [docs/metric_evaluation.md](docs/metric_evaluation.md). Use `metric-evaluation-index`, `metric-evaluation-health`, and `metric-evaluation-status` to discover, safety-check, and summarize those artifacts. The workflow can create `METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED` structural planning artifacts with explicit allow. It does not compute metrics, does not create metric/evaluation result rows, does not execute evaluation, does not create training_result, does not train weights, does not create model_version, does not optimize thresholds, does not create predictions, does not create calibrated probabilities, does not create feature importance, does not create active stock profiles, does not create real buy-review eligibility, does not apply paper approval, does not claim strategy performance validation, and does not authorize trading. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `metric-computation` to create report-only historical metric computation artifacts from approved Metric / Evaluation Phase 1 planning context and bounded Training / Evaluation sample rows; see [docs/metric_computation.md](docs/metric_computation.md). Use `metric-computation-index`, `metric-computation-health`, and `metric-computation-status` to discover, safety-check, and summarize those artifacts. The workflow can reach `READY_FOR_METRIC_COMPUTATION` without explicit allow, and can create `METRIC_COMPUTATION_REPORT_CREATED` artifacts with explicit allow for a bounded sample and the allowed first metric set only: `sample_count`, `label_coverage`, `average_return`, `median_return`, and `hit_rate`. It is not strategy performance validation, not training_result, not weights, not model_version, not thresholds, not predictions, not calibrated probabilities, not feature importance, not stock_profile, not buy-review, not paper approval, and not trading. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `metric-extension` to create report-only historical metric extension artifacts from approved Metric Computation Phase 1 context and bounded benchmark/industry mappings; see [docs/metric_extension.md](docs/metric_extension.md). Use `metric-extension-index`, `metric-extension-health`, and `metric-extension-status` to discover, safety-check, and summarize those artifacts. The workflow can reach `READY_FOR_METRIC_EXTENSION` without explicit allow, and can create `METRIC_EXTENSION_REPORT_CREATED` artifacts with explicit allow for the allowed extension metric set only. It is not performance validation, not a training result, does not create weights, does not create model versions, does not create thresholds, does not create predictions or probabilities, does not create feature importance, does not create stock profiles, does not create buy-review eligibility, does not approve paper trading, does not allow live trading, does not call broker APIs, does not place orders, and does not send messages. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `training-result-planning` to create report-only planning artifacts for a future training result workflow from approved metric extension, metric computation, metric evaluation, training evaluation, forward return label, and replay decision freeze context; see [docs/training_result_planning.md](docs/training_result_planning.md). Use `training-result-planning-index`, `training-result-planning-health`, and `training-result-planning-status` to discover, safety-check, and summarize those artifacts. The workflow can reach `READY_FOR_TRAINING_RESULT_PLANNING` without explicit allow, and can create `TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED` artifacts with explicit allow only. It is not actual training_result, does not train weights, does not create model_version, does not create parameter_version, does not optimize thresholds, does not create predictions, does not create calibrated probabilities, does not create feature importance, does not create active stock profiles, does not create real buy-review eligibility, does not apply paper approval, does not claim strategy performance validation, and does not authorize trading. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `training-result` to create report-only Actual Training Result Phase 1 metric evidence artifacts after explicit approval and complete upstream report-only lineage; see [docs/training_result.md](docs/training_result.md). Use `training-result-index`, `training-result-health`, and `training-result-status` to discover, safety-check, and summarize those artifacts. `TRAINING_RESULT_CREATED` means bounded report-only actual training_result artifacts exist for audit. It is not weights, not model_version, not parameter_version, not thresholds, not predictions, not calibrated probabilities, not feature importance, not stock_profile, not buy-review, not paper approval, not performance validation, and not trading. `research-status` includes the latest actual training_result context, metric evidence counts, source lineage, report path, next action, and safety flags while preserving later `PAPER_WORKFLOW_READY` priority.

Use `model-weight-versioning` to create report-only Model Weights / Versioning / Threshold / Prediction Phase 1 research artifacts after explicit approval and complete upstream report-only lineage; see [docs/model_weight_versioning.md](docs/model_weight_versioning.md). Use `model-weight-versioning-index`, `model-weight-versioning-health`, and `model-weight-versioning-status` to discover, safety-check, and summarize those artifacts. `MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED` means research references and metadata exist for audit only: it is not an active model, not a promoted model, not a production model, not active parameters, not active thresholds, not advisory predictions, not active probabilities, not active feature importance, not stock_profile, not buy-review, not paper approval, not performance validation, and not trading. `research-status` includes the latest model workflow context, artifact flags, source lineage, report path, next action, and safety flags while preserving later `PAPER_WORKFLOW_READY` priority.

Use `active-model` to create report-only Active Model Phase 1 research-governed artifacts after explicit approval and complete model-weight-versioning lineage; see [docs/active_model.md](docs/active_model.md). Use `active-model-index`, `active-model-health`, and `active-model-status` to discover, safety-check, and summarize those artifacts. `ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED` means research-governed active-model reference artifacts exist for audit only: it is not active production serving, not promoted model, not production model, not active thresholds, not advisory predictions, not active probabilities, not stock_profile, not buy-review, not paper approval, not performance validation, not current-candidates, not snapshot, not signal_semantics, and not trading. `research-status` includes the latest active-model run id, status/stage, health, source model workflow lineage, model reference ids, artifact flags, report path, next action, and downstream safety flags while preserving later `PAPER_WORKFLOW_READY` priority.

Use `stock-profile` to create report-only Stock Profile Phase 1 research-governed artifacts after explicit approval and complete active-model/model-weight-versioning lineage; see [docs/stock_profile.md](docs/stock_profile.md). Use `stock-profile-index`, `stock-profile-health`, and `stock-profile-status` to discover, safety-check, and summarize those artifacts. `STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED` means stock-profile research artifacts exist for audit only: it is not active stock_profile, not real buy-review, not paper approval, not performance validation, not current-candidates, not snapshot, not signal_semantics, not promoted model, not production model, not active thresholds, not advisory predictions, not active probabilities, and not trading. `research-status` includes the latest stock-profile run id, status/stage, health, source active-model/model-weight-versioning lineage, model reference ids, artifact flags, report path, next action, and downstream safety flags while preserving later `PAPER_WORKFLOW_READY` priority.

Use `paper-workflow-phase1` to create report-only Paper Workflow Phase 1 research-governed artifacts after explicit approval and complete stock-profile, active-model, and model-weight-versioning lineage; see [docs/paper_workflow_phase1.md](docs/paper_workflow_phase1.md). Use `paper-workflow-phase1-index`, `paper-workflow-phase1-health`, and `paper-workflow-phase1-status` to discover, safety-check, and summarize those artifacts. `PAPER_WORKFLOW_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED` means paper workflow metadata, lineage, review-context, draft, queue, limitations, warning, and safety artifacts exist for audit only: it is not APPROVED_FOR_PAPER, not real buy-review, not strategy performance validation, not current-candidates, not snapshot, not signal_semantics, not active stock_profile, not promoted model, not production model, not active thresholds, not advisory predictions, not active probabilities, and not trading. `research-status` includes the latest Paper Workflow Phase 1 run id, status/stage, health, source lineage, report path, next action, and downstream safety flags while preserving later `PAPER_WORKFLOW_READY` priority.

Use `approved-for-paper-phase1` to create scoped report-only APPROVED_FOR_PAPER Phase 1 artifacts after explicit approval and complete Paper Workflow Phase 1 lineage; see [docs/approved_for_paper_phase1.md](docs/approved_for_paper_phase1.md). Use `approved-for-paper-phase1-index`, `approved-for-paper-phase1-health`, and `approved-for-paper-phase1-status` to discover, safety-check, and summarize those artifacts. `APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED` means scoped metadata, lineage, review-context, decision-draft, limitation, warning, safety, and gate/precondition artifacts exist for audit only: it is not global APPROVED_FOR_PAPER, not real buy-review, not strategy performance validation, not current-candidates, not snapshot, not signal_semantics, not active stock_profile, not promoted model, not production model, not active thresholds, not advisory predictions, not active probabilities, and not trading. `research-status` includes the latest scoped APPROVED_FOR_PAPER Phase 1 run id, status/stage, health, source lineage, report path, next action, and downstream safety flags while preserving existing paper workflow priority.

Use `operational-global-approved-for-paper` to create report-only Operational Global APPROVED_FOR_PAPER planning artifacts after explicit approval and complete global approval-review lineage; see [docs/operational_global_approved_for_paper.md](docs/operational_global_approved_for_paper.md). Use `operational-global-approved-for-paper-index`, `operational-global-approved-for-paper-health`, and `operational-global-approved-for-paper-status` to discover, safety-check, and summarize those planning artifacts. `OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED` means operational planning artifacts exist for audit only: it does not grant operational global APPROVED_FOR_PAPER, is not real buy-review eligibility, does not set buy_review_allowed, is not strategy performance validation, does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, does not authorize active stock_profile, does not authorize promoted/production models, does not authorize active thresholds, does not authorize advisory predictions/probabilities, and does not authorize broker/order/message/API/trading. `research-status` includes the latest operational planning run id, status/stage, health, scope/expiry/revocation context, report path, next action, and downstream safety flags while preserving existing paper workflow priority.

Use `source-registry-schema-fixture` to create report-only synthetic Source Registry Schema Fixture artifacts for schema governance; see [docs/source_registry_schema_fixture.md](docs/source_registry_schema_fixture.md). Use `source-registry-schema-fixture-index`, `source-registry-schema-fixture-health`, and `source-registry-schema-fixture-status` to discover, safety-check, and summarize those fixture artifacts. `SOURCE_REGISTRY_SCHEMA_FIXTURE_CREATED` means synthetic schema fixture rows exist for audit only: it does not create real source permissions, does not create production source registry state, does not fetch real data, does not write data/raw, does not write data/processed, does not write data/cache, is not real buy-review eligibility, does not set buy_review_allowed, is not strategy performance validation, does not authorize current-candidates, does not authorize snapshots, does not authorize signal_semantics mutation, does not authorize active stock_profile, does not authorize promoted/production models, does not authorize active thresholds, does not authorize advisory predictions/probabilities, and does not authorize broker/order/message/API/trading. `research-status` includes the latest fixture run id, status/stage, health, artifact path, source count, validation issue count, report path, next action, and downstream safety flags while preserving existing paper workflow priority.

Use `raw-document-store-schema-fixture` to create synthetic/report-only Raw Document Store Schema Fixture artifacts for raw document and dataset-reference schema governance; see [docs/raw_document_store_schema_fixture.md](docs/raw_document_store_schema_fixture.md). Use `raw-document-store-schema-fixture-index`, `raw-document-store-schema-fixture-health`, and `raw-document-store-schema-fixture-status` to discover, safety-check, and summarize those fixture artifacts. `RAW_DOCUMENT_STORE_SCHEMA_FIXTURE_CREATED` is not production raw_document_store, not real data fetch, not raw document ingestion, not real source permission, does not write data/raw, does not write data/processed, does not write data/cache, does not create factor observations, does not create event ingestion, does not create company exposure, does not create replay evidence bundles, does not create buy-review eligibility, does not set buy_review_allowed, is not strategy performance validation, and does not authorize broker/order/message/API/trading. `research-status` includes this fixture context while preserving existing paper workflow priority. The Quant Research Design Pack v0.1 and Algorithm Timing Guard are recorded in [docs/quant_research_design_pack_v0_1.md](docs/quant_research_design_pack_v0_1.md).

Use `factor-definition-schema-fixture` to create synthetic/report-only Factor Definition Schema Fixture artifacts for factor-definition observation-rule schema governance; see [docs/factor_definition_schema_fixture.md](docs/factor_definition_schema_fixture.md). Use `factor-definition-schema-fixture-index`, `factor-definition-schema-fixture-health`, and `factor-definition-schema-fixture-status` to discover, safety-check, and summarize those fixture artifacts. `FACTOR_DEFINITION_SCHEMA_FIXTURE_CREATED` means synthetic factor-definition rows exist for audit only: it does not create an active factor library, factor observations, real factor observations, event ingestion, company exposure, replay evidence bundles, signal_score implementation, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review eligibility, buy_review_allowed, strategy performance validation, current-candidates, snapshots, signal_semantics mutation, advisory predictions/probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes. The 8-layer taxonomy is the primary classification; the fixed 12-factor framework remains a coverage checklist only. `research-status` includes this fixture context while preserving existing paper workflow priority and the Algorithm Timing Guard.

Use `company-exposure-schema-fixture` to create synthetic/report-only Company Exposure Schema Fixture artifacts for company exposure mapping schema governance; see [docs/company_exposure_schema_fixture.md](docs/company_exposure_schema_fixture.md). Use `company-exposure-schema-fixture-index`, `company-exposure-schema-fixture-health`, and `company-exposure-schema-fixture-status` to discover, safety-check, and summarize those fixture artifacts. `COMPANY_EXPOSURE_SCHEMA_FIXTURE_CREATED` means synthetic company exposure rows exist for audit only: it does not create production exposure mappings, active exposure mappings, company knowledge graphs, real ETF holdings ingestion, supplier/customer graphs, factor observations, event ingestion, replay evidence bundles, signal_score implementation, model training inputs, active weights, active thresholds, stock_profile validation, paper validation, real buy-review eligibility, buy_review_allowed, strategy performance validation, current-candidates, snapshots, signal_semantics mutation, advisory predictions/probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes. Exposure strength, exposure measure, and mapping confidence are descriptive evidence context only, not model weights, return probabilities, portfolio weights, signal weights, thresholds, or trading weights. `research-status` includes this fixture context while preserving existing paper workflow priority and the Algorithm Timing Guard.

Use `replay-decision-schema-fixture` to create synthetic/report-only Replay Decision Schema Fixture artifacts for replay decision schema governance; see [docs/replay_decision_schema_fixture.md](docs/replay_decision_schema_fixture.md). Use `replay-decision-schema-fixture-index`, `replay-decision-schema-fixture-health`, and `replay-decision-schema-fixture-status` to discover, safety-check, and summarize those fixture artifacts. `REPLAY_DECISION_SCHEMA_FIXTURE_CREATED` means synthetic replay decision rows exist for audit only: it does not create real replay decisions, does not consume real replay evidence bundles, does not create forward labels or future label joins, does not authorize signal_score inputs, model training inputs, active weights, active thresholds, stock_profile validation, paper validation, real buy-review eligibility, buy_review_allowed, strategy performance validation, current-candidates, snapshots, signal_semantics mutation, advisory predictions/probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes. `research-status` includes this fixture context while preserving existing paper workflow priority and the Algorithm Timing Guard.

Use `forward-return-label-schema-fixture` to create synthetic/report-only Forward Return Label Schema Fixture artifacts for label schema governance; see [docs/forward_return_label_schema_fixture.md](docs/forward_return_label_schema_fixture.md). Use `forward-return-label-schema-fixture-index`, `forward-return-label-schema-fixture-health`, and `forward-return-label-schema-fixture-status` to discover, safety-check, and summarize those fixture artifacts. `FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED` means synthetic forward label rows exist for audit only: it does not create real forward labels, does not join future labels to decision inputs, does not authorize signal_score inputs, does not authorize model training inputs, does not create active weights, active thresholds, stock_profile validation, paper validation, real buy-review eligibility, buy_review_allowed, strategy performance validation, current-candidates, snapshots, signal_semantics mutation, advisory predictions/probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes. `research-status` includes this fixture context while preserving existing paper workflow priority and the Algorithm Timing Guard.

Use `reviewed-local-csv-replay-prototype-input-contract-fixture` to create synthetic/report-only Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture artifacts for future reviewed local CSV replay input contract governance; see [docs/reviewed_local_csv_replay_prototype_input_contract_fixture.md](docs/reviewed_local_csv_replay_prototype_input_contract_fixture.md). Use `reviewed-local-csv-replay-prototype-input-contract-fixture-index`, `reviewed-local-csv-replay-prototype-input-contract-fixture-health`, and `reviewed-local-csv-replay-prototype-input-contract-fixture-status` to discover, safety-check, and summarize those fixture artifacts. `REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED` means synthetic contract rows exist for audit only: it does not create real reviewed CSV packages, PIT admissibility validators, real replay inputs, evidence bundles, decisions, freezes, forward labels, future-label joins, training datasets, metric computation, signal_score inputs, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review eligibility, buy_review_allowed, strategy performance validation, current-candidates, snapshots, signal_semantics mutation, advisory predictions/probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes. `research-status` includes this fixture context while preserving existing paper workflow priority and the Algorithm Timing Guard.

Use `tiny-pit-admissibility-validator-contract-fixture` to create synthetic/report-only Tiny PIT Admissibility Validator Contract Fixture artifacts for future PIT admissibility validator contract governance; see [docs/tiny_pit_admissibility_validator_contract_fixture.md](docs/tiny_pit_admissibility_validator_contract_fixture.md). Use `tiny-pit-admissibility-validator-contract-fixture-index`, `tiny-pit-admissibility-validator-contract-fixture-health`, and `tiny-pit-admissibility-validator-contract-fixture-status` to discover, safety-check, and summarize those fixture artifacts. `TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED` means synthetic contract rows exist for audit only: it is not a real PIT validator, does not create real reviewed CSV packages, active reviewed input candidates, real replay inputs, evidence bundles, decisions, freezes, forward labels, future-label joins, training datasets, metric computation, signal_score inputs, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review eligibility, buy_review_allowed, strategy performance validation, current-candidates, snapshots, signal_semantics mutation, advisory predictions/probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes. `research-status` includes this fixture context while preserving existing paper workflow priority and the Algorithm Timing Guard.

Use `tiny-pit-admissibility-validator` to create synthetic/report-only Tiny PIT Admissibility Validator artifacts for future PIT admissibility validator governance; see [docs/tiny_pit_admissibility_validator.md](docs/tiny_pit_admissibility_validator.md). Use `tiny-pit-admissibility-validator-index`, `tiny-pit-admissibility-validator-health`, and `tiny-pit-admissibility-validator-status` to discover, safety-check, and summarize those synthetic validator artifacts. `TINY_PIT_ADMISSIBILITY_VALIDATOR_SYNTHETIC_CORE_CREATED` means synthetic package cases were evaluated for diagnostics only: it is not a real PIT validator, does not create real reviewed CSV packages, active reviewed input candidates, real replay inputs, active replay input, replay execution, evidence bundles, decisions, freezes, forward labels, future-label joins, training datasets, metric computation, signal_score inputs, model training, active weights, active thresholds, stock_profile validation, paper validation, real buy-review eligibility, buy_review_allowed, strategy performance validation, current-candidates, snapshots, signal_semantics mutation, advisory predictions/probabilities, broker/order/message/API/trading, or data/raw, data/processed, or data/cache writes. `research-status` includes this synthetic validator context while preserving existing paper workflow priority and the Algorithm Timing Guard.

Use `active-replay-input-promotion` to create report-only promotion readiness context for a validator/smoke pass-candidate plus explicit local promotion request and human-review manifests; see [docs/active_replay_input_promotion.md](docs/active_replay_input_promotion.md). Use `active-replay-input-promotion-index`, `active-replay-input-promotion-health`, and `active-replay-input-promotion-status` to discover, safety-check, and summarize promotion artifacts. `PROMOTION_READY_FOR_HUMAN_REVIEW` is not active replay input and not `ACTIVE_REPLAY_INPUT_READY`: it does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, and does not create real buy-review eligibility. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `active-replay-input-acceptance` to create report-only acceptance governance context for a promotion-ready artifact plus explicit reviewer authority, manual attestation, second-review, and red-team manifests; see [docs/active_replay_input_acceptance.md](docs/active_replay_input_acceptance.md). Use `active-replay-input-acceptance-index`, `active-replay-input-acceptance-health`, and `active-replay-input-acceptance-status` to discover, safety-check, and summarize acceptance artifacts. `ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW` is not active replay input and not `ACTIVE_REPLAY_INPUT_READY`: it does not create active replay input, does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, and does not create real buy-review eligibility. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `active-replay-input-active-ready` to create report-only active-ready governance context for an accepted artifact plus explicit final-review manifests; see [docs/active_replay_input_active_ready.md](docs/active_replay_input_active_ready.md). Use `active-replay-input-active-ready-index`, `active-replay-input-active-ready-health`, and `active-replay-input-active-ready-status` to discover, safety-check, and summarize active-ready artifacts. `ACTIVE_READY_READY_FOR_FINAL_REVIEW` is not active replay input and not `ACTIVE_REPLAY_INPUT_READY`: it does not create active replay input, does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not authorize trading. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `active-replay-input-final-review` to create report-only final-review governance context for an active-ready artifact plus explicit final reviewer manifests; see [docs/active_replay_input_final_review.md](docs/active_replay_input_final_review.md). Use `active-replay-input-final-review-index`, `active-replay-input-final-review-health`, and `active-replay-input-final-review-status` to discover, safety-check, and summarize final-review artifacts. `FINAL_REVIEW_READY_FOR_EMISSION_REVIEW` is not active replay input and not `ACTIVE_REPLAY_INPUT_READY`: it does not create active replay input, does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not authorize trading. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `active-replay-input-emission` to create report-only emission governance context for a final-review artifact plus explicit emission request and reviewer manifests; see [docs/active_replay_input_emission.md](docs/active_replay_input_emission.md). Use `active-replay-input-emission-index`, `active-replay-input-emission-health`, and `active-replay-input-emission-status` to discover, safety-check, and summarize emission artifacts. `EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW` is not active replay input and not `ACTIVE_REPLAY_INPUT_READY`: it does not emit `ACTIVE_REPLAY_INPUT_READY`, does not create active replay input, does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not authorize trading. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `active-replay-input-ready-decision` to create report-only ready-decision governance context for an emission-ready artifact plus explicit decision request, reviewer authority, attestation, PIT/source evidence, taxonomy evidence, leakage/side-effect evidence, and overclaim guards; see [docs/active_replay_input_ready_decision.md](docs/active_replay_input_ready_decision.md). Use `active-replay-input-ready-decision-index`, `active-replay-input-ready-decision-health`, and `active-replay-input-ready-decision-status` to discover, safety-check, and summarize ready-decision artifacts. `READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION` is not active replay input and not `ACTIVE_REPLAY_INPUT_READY`: it does not emit `ACTIVE_REPLAY_INPUT_READY`, does not create active replay input, does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not authorize trading. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `active-replay-input-ready-emission` to create report-only `ACTIVE_REPLAY_INPUT_READY` emission-decision context for ready-to-emit active-ready evidence plus final emission request, reviewer authority, attestation, PIT/source evidence, taxonomy evidence, leakage/side-effect evidence, and overclaim guards; see [docs/active_replay_input_ready_emission.md](docs/active_replay_input_ready_emission.md). Use `active-replay-input-ready-emission-index`, `active-replay-input-ready-emission-health`, and `active-replay-input-ready-emission-status` to discover, safety-check, and summarize emission-decision artifacts. `READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION` is not active replay input and not `ACTIVE_REPLAY_INPUT_READY`: it does not emit `ACTIVE_REPLAY_INPUT_READY`, does not create active replay input, does not run replay, does not create replay decisions, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not authorize trading. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `active-replay-input-ready-actual-emission` to create report-only actual `ACTIVE_REPLAY_INPUT_READY` marker-only diagnostics after explicit governance checks and an explicit allow flag; see [docs/active_replay_input_ready_actual_emission.md](docs/active_replay_input_ready_actual_emission.md). Use `active-replay-input-ready-actual-emission-index`, `active-replay-input-ready-actual-emission-health`, and `active-replay-input-ready-actual-emission-status` to discover, safety-check, and summarize marker-only actual-emission artifacts. Marker-only `ACTIVE_REPLAY_INPUT_READY` does not create active replay input, does not run replay, does not create replay decisions, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not authorize trading. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `active-replay-input-create` to create a governed report-only active replay input artifact after marker-only `ACTIVE_REPLAY_INPUT_READY` lineage and explicit creation evidence; see [docs/active_replay_input_create.md](docs/active_replay_input_create.md). Use `active-replay-input-create-index`, `active-replay-input-create-health`, and `active-replay-input-create-status` to discover, safety-check, and summarize creation artifacts. `ACTIVE_REPLAY_INPUT_CREATED` can exist only as a report-only diagnostics artifact when the explicit allow flag is used. Active replay input creation does not run replay, does not create replay decisions, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not authorize trading. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `real-replay-execute` to run report-only real replay execution prechecks for an active replay input; see [docs/real_replay_execute.md](docs/real_replay_execute.md). Use `real-replay-execute-index`, `real-replay-execute-health`, and `real-replay-execute-status` to discover, safety-check, and summarize pre-execution review artifacts. `READY_FOR_REAL_REPLAY_EXECUTION_REVIEW` means pre-execution review only: it does not run replay, does not create replay decisions, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not authorize trading. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `actual-replay-execute` to create report-only actual replay execution artifacts after explicit governance inputs; see [docs/actual_replay_execute.md](docs/actual_replay_execute.md). Use `actual-replay-execute-index`, `actual-replay-execute-health`, and `actual-replay-execute-status` to discover, safety-check, and summarize execution artifacts. `ACTUAL_REPLAY_EXECUTED` means execution artifacts only: it is not replay_decision creation, no forward labels are computed, no training runs, no active stock_profile is created, no real buy-review eligibility is created, and no trading is authorized. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `replay-decision-freeze` to create report-only frozen decision-time review rows after actual replay execution context and explicit freeze governance inputs; see [docs/replay_decision_freeze.md](docs/replay_decision_freeze.md). Use `replay-decision-freeze-index`, `replay-decision-freeze-health`, and `replay-decision-freeze-status` to discover, safety-check, and summarize freeze artifacts. The workflow can reach `READY_FOR_REPLAY_DECISION_FREEZE` without an allow flag and can produce `REPLAY_DECISION_FROZEN` with explicit allow. `REPLAY_DECISION_FROZEN` means frozen decision-time review rows only: it does not compute forward labels or future returns, does not create forward_return_label artifacts, does not train weights, does not create training_result, does not create active stock_profile, does not create real buy-review eligibility, does not apply paper approval, does not validate strategy performance, and does not authorize trading. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `active-replay-input-ready` to create report-only `ACTIVE_REPLAY_INPUT_READY` governance context for a ready-decision artifact plus final authority, attestation, PIT/source, taxonomy, leakage/side-effect, and overclaim evidence; see [docs/active_replay_input_ready.md](docs/active_replay_input_ready.md). Use `active-replay-input-ready-index`, `active-replay-input-ready-health`, and `active-replay-input-ready-status` to discover, safety-check, and summarize active-ready workflow artifacts. `READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY` is not `ACTIVE_REPLAY_INPUT_READY`: it does not emit `ACTIVE_REPLAY_INPUT_READY`, does not create active replay input, does not run replay, does not create replay decisions, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not authorize trading. `research-status` includes this context while preserving later `PAPER_WORKFLOW_READY` priority.

Use `pit-official-status-evidence-packet-enrichment-index`, `pit-official-status-evidence-packet-enrichment-health`, and `pit-official-status-evidence-packet-enrichment-status` to discover, safety-check, and summarize enrichment artifacts. `research-status` includes the latest enrichment context, including strong same-date quotation counts, reviewed no-hit support counts, reviewer-acceptance-required counts, checklist-pass counts, and remaining blocked counts while preserving later paper workflow priority.

Use `reviewer-no-hit-source-coverage-acceptance` to create report-only reviewer acceptance templates for official no-hit source coverage, query windows, inference limits, and survivorship rationale; see [docs/reviewer_no_hit_source_coverage_acceptance.md](docs/reviewer_no_hit_source_coverage_acceptance.md). Accepted rows remain supporting context only and do not approve PIT rows, create clean review updates, export universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, or compute labels.

Use `reviewer-no-hit-source-coverage-acceptance-index`, `reviewer-no-hit-source-coverage-acceptance-health`, and `reviewer-no-hit-source-coverage-acceptance-status` to discover, safety-check, and summarize acceptance artifacts. `research-status` includes the latest reviewer no-hit acceptance context, including accepted supporting-context counts, reviewer-required counts, survivorship-rationale-required counts, checklist-pass counts, and remaining blocked counts while preserving later paper workflow priority.

Use `reviewer-no-hit-acceptance-downstream-impact` to link reviewer-accepted no-hit supporting context into downstream packet/checklist/policy impact reporting; see [docs/reviewer_no_hit_acceptance_downstream_impact.md](docs/reviewer_no_hit_acceptance_downstream_impact.md). Its index, health, and status commands make this report-only impact visible in `research-status` without creating PIT approvals, clean review updates, export readiness, staging, current-candidates outputs, snapshots, or forward labels.

Use `first-batch-reviewer-evidence-completion-plan` to turn first-batch PIT evidence gaps into manual completion templates and TODO matrices; see [docs/first_batch_reviewer_evidence_completion_plan.md](docs/first_batch_reviewer_evidence_completion_plan.md). Its index, health, and status commands make first-batch manual evidence requirements visible in `research-status` without approving rows, creating clean review updates, exporting universe files, running current-candidates, building snapshots, or computing forward labels.

Use `first-batch-partial-completion-impact` to compare diagnostics-only partial reviewer completion fixtures against the first-batch completion plan; see [docs/first_batch_partial_completion_impact.md](docs/first_batch_partial_completion_impact.md). Its index, health, and status commands make blocker deltas visible in `research-status` without approving rows, setting `include_flag=true`, setting `valid_for_signal_date=true`, creating clean review updates, exporting universe files, running current-candidates, building snapshots, or computing forward labels.

Use `material-pit-evidence-gate-closure-plan` to convert first-batch material PIT blockers into reviewer closure-path planning matrices; see [docs/material_pit_evidence_gate_closure_plan.md](docs/material_pit_evidence_gate_closure_plan.md). Its index, health, and status commands make reusable symbol-level, date-specific, reviewer no-hit, survivorship, metadata, and stock ST/no-ST closure requirements visible in `research-status` without approving rows, creating clean review updates, exporting universe files, running current-candidates, building snapshots, or computing forward labels.

Use `reviewer-material-evidence-fill-guidance` to turn the material gate closure plan into report-only human reviewer fill guidance; see [docs/reviewer_material_evidence_fill_guidance.md](docs/reviewer_material_evidence_fill_guidance.md). Its index, health, and status commands make symbol-level, date-specific, no-hit, survivorship, and metadata fill guidance visible in `research-status` without approving rows, creating clean review updates, running PIT review/export/staging/current-candidates, writing data inputs, building snapshots, or computing labels.

Use `universe-profile-policy-audit` to classify local universe labels such as legacy mixed `etf_core`, report STOCK/ETF distribution, and produce future split guidance for `stock_core`, `etf_core`, and `mixed_demo_core`; see [docs/universe_profile_policy_audit.md](docs/universe_profile_policy_audit.md). The audit is report-only and does not approve/reject rows, export universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, or compute labels.

Use `universe-profile-policy-audit-index`, `universe-profile-policy-audit-health`, and `universe-profile-policy-audit-status` to discover, safety-check, and summarize universe profile policy audit artifacts. `research-status` includes this policy context, including mixed-universe and split-guidance counts, while preserving later paper workflow priority.

Use `universe-profile-split-worklist-plan` to apply `config/universe_profiles.yaml` to legacy mixed `etf_core` rows and produce future split-worklist guidance for `stock_core`, `etf_core`, and `mixed_demo_core`; see [docs/universe_profile_split_worklist_plan.md](docs/universe_profile_split_worklist_plan.md). The workflow is planning-only and does not mutate active worklists, approve/reject rows, export universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, or compute labels.

Use `universe-profile-split-worklist-plan-index`, `universe-profile-split-worklist-plan-health`, and `universe-profile-split-worklist-plan-status` to discover, safety-check, and summarize split-worklist plan artifacts. `research-status` includes the latest split plan as universe-profile planning context, including profile-conflict counts and recommended future universe counts, while preserving later paper workflow priority.

Use `reviewed-replacement-worklist-plan` to create report-only future replacement templates for `stock_core`, `etf_core`, and `mixed_demo_core`; see [docs/reviewed_replacement_worklist_plan.md](docs/reviewed_replacement_worklist_plan.md). The workflow leaves active legacy worklists unchanged and does not approve/reject rows, export universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, or compute labels.

Use `reviewed-replacement-worklist-plan-index`, `reviewed-replacement-worklist-plan-health`, and `reviewed-replacement-worklist-plan-status` to discover, safety-check, and summarize replacement-plan artifacts. `research-status` includes the latest replacement plan as planning context while preserving later paper workflow priority.

Use `reviewed-replacement-worklist-acceptance` to acknowledge reviewed replacement templates as planning context only; see [docs/reviewed_replacement_worklist_acceptance.md](docs/reviewed_replacement_worklist_acceptance.md). The command requires explicit manual acceptance metadata and still does not activate worklists, approve/reject PIT rows, export universe files, run current-candidates, build snapshots, or compute labels.

Use `reviewed-replacement-worklist-activation` to create a guarded activated replacement worklist planning artifact under `outputs/reports` only; see [docs/reviewed_replacement_worklist_activation.md](docs/reviewed_replacement_worklist_activation.md). The command requires explicit manual activation metadata and still does not mutate active legacy worklists, approve/reject PIT rows, export universe files, run current-candidates, build snapshots, or compute labels.

Use `activated-replacement-worklist-evidence-update-plan` to create profile-specific manual evidence update packages from an activation artifact; see [docs/activated_replacement_worklist_evidence_update_plan.md](docs/activated_replacement_worklist_evidence_update_plan.md). The workflow writes planning artifacts under `outputs/reports` only, keeps rows non-approved, and does not create clean review updates, export universe files, run current-candidates, build snapshots, or compute labels.

Use `activated-replacement-worklist-evidence-update-plan-index`, `activated-replacement-worklist-evidence-update-plan-health`, and `activated-replacement-worklist-evidence-update-plan-status` to discover, safety-check, and summarize evidence-update planning artifacts. `research-status` includes this context while preserving later paper workflow priority.

Use `reviewed-replacement-worklist-acceptance-index`, `reviewed-replacement-worklist-acceptance-health`, and `reviewed-replacement-worklist-acceptance-status` to discover, safety-check, and summarize acceptance artifacts. `research-status` includes acceptance context while preserving later paper workflow priority.

Use `universe-profile-split-worklist-plan` to apply `config/universe_profiles.yaml` and write report-only future split guidance for `stock_core`, `etf_core`, and `mixed_demo_core`; see [docs/universe_profile_split_worklist_plan.md](docs/universe_profile_split_worklist_plan.md). The planner leaves active worklists unchanged and does not approve/reject rows, export universe files, build snapshots, run current-candidates, or compute labels.

For the v1.8.0 checkpoint covering universe profile policy audit artifact views and `research-status` integration, see [docs/release_checkpoint_v1.8.0.md](docs/release_checkpoint_v1.8.0.md).

For the v1.3.0 checkpoint covering PIT universe evidence completion helper artifact views and `research-status` integration, see [docs/release_checkpoint_v1.3.0.md](docs/release_checkpoint_v1.3.0.md).

For the v1.4.0 checkpoint covering PIT universe export-readiness gate-ordering and required metadata consolidation tests, see [docs/release_checkpoint_v1.4.0.md](docs/release_checkpoint_v1.4.0.md).

For the v1.5.0 checkpoint covering PIT universe export staging artifact views and `research-status` integration, see [docs/release_checkpoint_v1.5.0.md](docs/release_checkpoint_v1.5.0.md).

For the v1.6.0 checkpoint covering PIT universe evidence review worklist artifact views and `research-status` integration, see [docs/release_checkpoint_v1.6.0.md](docs/release_checkpoint_v1.6.0.md).

For the v1.13.0 checkpoint covering activated replacement worklist evidence update planning and `research-status` integration, see [docs/release_checkpoint_v1.13.0.md](docs/release_checkpoint_v1.13.0.md).

For the v1.14.0 checkpoint covering PIT evidence checklist validation, artifact views, and `research-status` integration, see [docs/release_checkpoint_v1.14.0.md](docs/release_checkpoint_v1.14.0.md).

For the v1.19.0 checkpoint covering reviewer no-hit source coverage acceptance, artifact views, and `research-status` integration, see [docs/release_checkpoint_v1.19.0.md](docs/release_checkpoint_v1.19.0.md).

For the v1.20.0 checkpoint covering reviewer no-hit acceptance downstream impact artifact views and `research-status` integration, see [docs/release_checkpoint_v1.20.0.md](docs/release_checkpoint_v1.20.0.md).

For the v1.21.0 checkpoint covering first-batch reviewer evidence completion planning, artifact views, and `research-status` integration, see [docs/release_checkpoint_v1.21.0.md](docs/release_checkpoint_v1.21.0.md).

For the v1.22.0 checkpoint covering first-batch partial completion impact artifact views and `research-status` integration, see [docs/release_checkpoint_v1.22.0.md](docs/release_checkpoint_v1.22.0.md).

For the v1.23.0 checkpoint covering material PIT evidence gate closure plan artifact views and `research-status` integration, see [docs/release_checkpoint_v1.23.0.md](docs/release_checkpoint_v1.23.0.md).

For the v1.24.0 checkpoint covering reviewer material evidence fill guidance artifact views and `research-status` integration, see [docs/release_checkpoint_v1.24.0.md](docs/release_checkpoint_v1.24.0.md).

For the v1.25.0 checkpoint covering one-row material evidence fill package artifact views and `research-status` integration, see [docs/release_checkpoint_v1.25.0.md](docs/release_checkpoint_v1.25.0.md).

For the v1.34.0 checkpoint covering active replay input final-review artifact views and `research-status` integration, see [docs/release_checkpoint_v1.34.0.md](docs/release_checkpoint_v1.34.0.md).

For the v1.35.0 checkpoint covering active replay input emission artifact views and `research-status` integration, see [docs/release_checkpoint_v1.35.0.md](docs/release_checkpoint_v1.35.0.md).

For the v1.36.0 checkpoint covering active replay input ready-decision artifact views and `research-status` integration, see [docs/release_checkpoint_v1.36.0.md](docs/release_checkpoint_v1.36.0.md).

For the v1.39.0 checkpoint covering actual marker-only `ACTIVE_REPLAY_INPUT_READY` emission artifact views and `research-status` integration, see [docs/release_checkpoint_v1.39.0.md](docs/release_checkpoint_v1.39.0.md).

For the v1.28.0 checkpoint covering historical replay input gate validator fixture `research-status` integration, see [docs/release_checkpoint_v1.28.0.md](docs/release_checkpoint_v1.28.0.md).

For the v1.68.0 checkpoint covering Tiny PIT Admissibility Validator Contract Fixture `research-status` integration, see [docs/release_checkpoint_v1.68.0.md](docs/release_checkpoint_v1.68.0.md).

For the v1.29.0 checkpoint covering real historical replay input gate validator `research-status` integration, see [docs/release_checkpoint_v1.29.0.md](docs/release_checkpoint_v1.29.0.md).

For the v1.15.0 checkpoint covering EOD post-close low-budget PIT policy profile comparison and `research-status` integration, see [docs/release_checkpoint_v1.15.0.md](docs/release_checkpoint_v1.15.0.md).

For the v1.16.0 checkpoint covering PIT official status evidence packet artifacts and `research-status` integration, see [docs/release_checkpoint_v1.16.0.md](docs/release_checkpoint_v1.16.0.md).

For the v1.18.0 checkpoint covering PIT official status evidence packet enrichment and `research-status` integration, see [docs/release_checkpoint_v1.18.0.md](docs/release_checkpoint_v1.18.0.md).

For the v1.17.0 checkpoint covering reviewed no-hit support in PIT evidence policy profile comparison, see [docs/release_checkpoint_v1.17.0.md](docs/release_checkpoint_v1.17.0.md).

For the v1.7.0 checkpoint covering PIT universe evidence update ingestion artifact views and `research-status` integration, see [docs/release_checkpoint_v1.7.0.md](docs/release_checkpoint_v1.7.0.md).

For the v1.2.0 checkpoint covering PIT universe overlay export-readiness artifact views and `research-status` integration, see [docs/release_checkpoint_v1.2.0.md](docs/release_checkpoint_v1.2.0.md).

For the v1.1.0 checkpoint covering reviewed PIT universe overlay approval artifact views and `research-status` integration, see [docs/release_checkpoint_v1.1.0.md](docs/release_checkpoint_v1.1.0.md).

For the v1.0.0 checkpoint covering the plan-only path from warmup-aware backfill planning through PIT universe overlay preparation, see [docs/release_checkpoint_v1.0.0.md](docs/release_checkpoint_v1.0.0.md).

`research-status` includes the latest `current-candidates-backfill-plan-status` as planning context, including selected date count, first/last signal dates, warmup requirement, forward-horizon summary, health status, and report path. The plan is visible but does not imply candidate generation; later paper workflow priority is preserved. See [docs/local_research_dashboard.md#current-candidates-backfill-plan-status](docs/local_research_dashboard.md#current-candidates-backfill-plan-status).

For turning current-candidates artifacts into local advisory signals and alert previews without message delivery or execution, see [docs/signal_advisory.md](docs/signal_advisory.md).

For the deterministic policy that maps candidate/scored rows into safe advisory labels such as `DEMO_ONLY`, `WATCH`, and `REVIEW_BUY_CANDIDATE`, see [docs/signal_semantics.md](docs/signal_semantics.md). Demo rows remain workflow validation only, and all labels require manual confirmation with auto-order disabled.

For local threshold analysis of proposed non-demo advisory profiles before wiring them into product semantics, use `advisory-profile-calibration`; see [docs/advisory_profile_calibration.md](docs/advisory_profile_calibration.md). It produces simulated calibration labels only and never creates orders, broker calls, or real message delivery. To discover, check, and summarize these calibration artifacts, use `advisory-profile-calibration-index`, `advisory-profile-calibration-health`, and `advisory-profile-calibration-status`.

To compare calibration artifacts against current `signal_semantics` defaults without changing thresholds, use `calibration-to-signal-semantics`; see [docs/calibration_to_signal_semantics.md](docs/calibration_to_signal_semantics.md). The report is proposal-only and currently favors keeping defaults, collecting more evidence, and expanding `WATCH` semantics before any non-demo buy-review expansion. Use `calibration-to-signal-semantics-index`, `calibration-to-signal-semantics-health`, and `calibration-to-signal-semantics-status` to discover, safety-check, and summarize those proposal artifacts.

`research-status` includes the latest `calibration-to-signal-semantics-status` as proposal/design context, including proposal categories, `defaults_changed`, observed calibration label counts, report path, and next action. This does not validate strategy performance or change defaults; later workflow priority is preserved. See [docs/local_research_dashboard.md#calibration-to-signal-semantics-status](docs/local_research_dashboard.md#calibration-to-signal-semantics-status).

`research-status` includes the latest `advisory-profile-calibration-status` as calibration/design context, including profile, health status, simulated label counts, report path, and next action. `REVIEW_BUY_CANDIDATE` remains human-review-only and later paper workflow priority is preserved; see [docs/local_research_dashboard.md#advisory-profile-calibration-status](docs/local_research_dashboard.md#advisory-profile-calibration-status).

Downstream advisory artifacts record shared `signal_semantics` provenance metadata so audits can see which local policy/classifier produced each advisory action. Provenance is not a trading approval; health checks warn on legacy missing provenance and fail unsafe provenance such as auto-order, live trading, broker access, or unexpected policy source.

To discover, check, and summarize local signal semantics artifacts before wiring semantics into broader advisory or dashboard flows, use `signal-semantics-index`, `signal-semantics-health`, and `signal-semantics-status`; see [docs/signal_semantics.md#index-health-and-status](docs/signal_semantics.md#index-health-and-status).

`research-status` includes the latest `signal-semantics-status` as advisory-policy context, including action counts, health status, profile, input path, and report path. `REVIEW_BUY_CANDIDATE` remains a human-review label, not an order, while later paper workflow priority is preserved; see [docs/local_research_dashboard.md#signal-semantics-status](docs/local_research_dashboard.md#signal-semantics-status).

To discover, check, and summarize local signal advisory artifacts before any future alert-delivery work, use `signal-advisory-index`, `signal-advisory-health`, and `signal-advisory-status`; see [docs/signal_advisory.md#index-health-and-status](docs/signal_advisory.md#index-health-and-status).

`research-status` includes the latest `signal-advisory-status` as advisory context, including signal counts, demo-only state, health status, and local alert-preview path, while preserving later paper workflow priority; see [docs/local_research_dashboard.md#signal-advisory-status](docs/local_research_dashboard.md#signal-advisory-status).

For asking a focused local question about one symbol from existing candidate or signal artifacts, use `single-symbol-advisory`; see [docs/single_symbol_advisory.md](docs/single_symbol_advisory.md).

For a local deterministic answer to a user-style question such as "should I buy?", add `--question-style` to `single-symbol-advisory`; see [docs/single_symbol_advisory.md#question-style-answer](docs/single_symbol_advisory.md#question-style-answer). This is not LLM-based and does not send messages or place orders.

To discover, check, and summarize deterministic question-style answer artifacts, use `single-symbol-advisory-answer-index`, `single-symbol-advisory-answer-health`, and `single-symbol-advisory-answer-status`; see [docs/single_symbol_advisory.md#question-style-answer-index-health-and-status](docs/single_symbol_advisory.md#question-style-answer-index-health-and-status).

`research-status` includes the latest `single-symbol-advisory-answer-status` as question-style advisory context, including the latest answered symbol, answer action, health status, demo safety flags, and local markdown answer path, while preserving later paper workflow priority; see [docs/local_research_dashboard.md#single-symbol-advisory-answer-status](docs/local_research_dashboard.md#single-symbol-advisory-answer-status).

For simple Chinese/English user-style questions such as `000001 现在能不能买？` or `Should I sell 510300?`, use `advisory-conversation`; see [docs/advisory_conversation.md](docs/advisory_conversation.md). This is deterministic local parsing and routing only: no LLM/API calls, no message delivery, no broker access, and no order placement.

To discover, check, and summarize local conversational advisory runs, use `advisory-conversation-index`, `advisory-conversation-health`, and `advisory-conversation-status`; see [docs/advisory_conversation.md#index-health-and-status](docs/advisory_conversation.md#index-health-and-status).

`research-status` includes the latest `advisory-conversation-status` as local conversational advisory context, including the original question, parsed symbol/intent, status, health status, no-LLM/no-message safety flags, and linked answer path, while preserving later paper workflow priority; see [docs/local_research_dashboard.md#advisory-conversation-status](docs/local_research_dashboard.md#advisory-conversation-status).

To discover, check, and summarize repeated single-symbol advisory reviews, use `single-symbol-advisory-index`, `single-symbol-advisory-health`, and `single-symbol-advisory-status`; see [docs/single_symbol_advisory.md#index-health-and-status](docs/single_symbol_advisory.md#index-health-and-status).

`research-status` includes the latest `single-symbol-advisory-status` as one-symbol advisory context, including the latest symbol, advisory action, health status, demo safety flags, and local alert preview path, while preserving later paper workflow priority; see [docs/local_research_dashboard.md#single-symbol-advisory-status](docs/local_research_dashboard.md#single-symbol-advisory-status).

For indexing generated current-candidate runs, see [docs/current_candidate_artifact_index.md](docs/current_candidate_artifact_index.md).

For checking generated current-candidate artifact health, see [docs/current_candidate_artifact_health.md](docs/current_candidate_artifact_health.md).

For handing a healthy current-candidate `candidates.csv` into daily paper trading, see [docs/current_to_paper_handoff.md](docs/current_to_paper_handoff.md).

For creating manual review update templates from paper decisions, see [docs/current_to_paper_review_handoff.md](docs/current_to_paper_review_handoff.md).

For validating edited paper review templates before applying them, see [docs/paper_review_template_health.md](docs/paper_review_template_health.md).

For multi-date replay runs and batch-level artifacts, see [docs/batch_replay.md](docs/batch_replay.md).

For explainable parameter comparison using batch replay outputs, see [docs/parameter_calibration.md](docs/parameter_calibration.md).

For account-level portfolio ledgers and equity-curve simulation, see [docs/portfolio_simulation.md](docs/portfolio_simulation.md).

For portfolio-aware batch replay and calibration ranking, see [docs/portfolio_aware_calibration.md](docs/portfolio_aware_calibration.md).

For train/validation/test calibration checks and overfitting diagnostics, see [docs/walk_forward_validation.md](docs/walk_forward_validation.md).

For reviewed candidate decision logs and manual hypothetical paper fills, see [docs/manual_paper_trading.md](docs/manual_paper_trading.md).

For manual approve/reject/watch review updates before fills, see [docs/paper_trading_review_workflow.md](docs/paper_trading_review_workflow.md).

For daily local paper-trading reports from candidate CSVs and manual fills, see [docs/daily_paper_trading_runner.md](docs/daily_paper_trading_runner.md).

For local paper-trading CLI commands, see [docs/paper_trading_cli.md](docs/paper_trading_cli.md).

For paper decision/fill reconciliation, see [docs/paper_fill_reconciliation.md](docs/paper_fill_reconciliation.md).

For the full local paper trading workflow smoke-test example, see [docs/paper_trading_e2e_workflow.md](docs/paper_trading_e2e_workflow.md).

For a consolidated local index of daily, review, and reconciliation artifacts, see [docs/paper_trading_artifact_index.md](docs/paper_trading_artifact_index.md).

For checking indexed artifact paths and metadata health, see [docs/paper_trading_artifact_health_check.md](docs/paper_trading_artifact_health_check.md).

For a one-page local workflow status dashboard and next manual action, see [docs/paper_trading_workflow_status.md](docs/paper_trading_workflow_status.md).

For local-safe raw data source adapters before ingestion, see [docs/data_sources.md](docs/data_sources.md).

For the project data-source roadmap across AKShare upstream routes, BaoStock, Tushare, professional vendors, and permanent `LOCAL_CSV` fallback, see [docs/data_source_strategy.md](docs/data_source_strategy.md).

For checking local source and upstream route availability before import, see [docs/data_source_health.md](docs/data_source_health.md).

For caching successful canonical daily market bars and querying them into local pipeline inputs, see [docs/market_data_cache.md](docs/market_data_cache.md).

For exporting reviewed source/upstream cache selections into one data-pipeline-ready market CSV, use `market-cache-export`; see [docs/market_cache_export.md](docs/market_cache_export.md).

For drafting reviewed cache export manifests from local cache coverage, source reliability policy, and inline source-comparison diagnostics, use `market-cache-export-plan`; the plan index/health/status views and unified `research-status` summarize comparison support before larger exports. See [docs/market_cache_export_policy.md](docs/market_cache_export_policy.md).

To discover, check, and summarize policy-aware cache export recommendation plans, use `market-cache-export-plan-index`, `market-cache-export-plan-health`, and `market-cache-export-plan-status`; see [docs/market_cache_export_policy.md#index-health-and-status](docs/market_cache_export_policy.md#index-health-and-status).

`research-status` includes the latest `market-cache-export-plan-status` as policy recommendation context, while still letting reviewed exports, current-candidates, market-update-handoff, historical-backfill context, and paper workflow artifacts take priority; see [docs/local_research_dashboard.md#market-cache-export-plan-status](docs/local_research_dashboard.md#market-cache-export-plan-status).

To discover, check, and summarize reviewed cache exports before downstream snapshot workflows, use `market-cache-export-index`, `market-cache-export-health`, and `market-cache-export-status`; see [docs/market_cache_export.md#index-health-and-status](docs/market_cache_export.md#index-health-and-status).

`research-status` includes the latest `market-cache-export-status` as reviewed cache-to-snapshot context, while still letting later current-candidates, market-update-handoff, or paper workflow artifacts take priority; see [docs/local_research_dashboard.md#market-cache-export-status](docs/local_research_dashboard.md#market-cache-export-status).

For source-policy-aware acceptance checks before ingesting market rows into the local cache, use `market-cache-preflight`; see [docs/market_cache_preflight.md](docs/market_cache_preflight.md).

For a dry-run-first local market update wrapper that runs preflight before optional cache ingest, use `market-daily-update`; see [docs/market_daily_update.md](docs/market_daily_update.md).

For a local-only historical backfill skeleton over a reviewed symbol/date manifest, use `historical-backfill`; see [docs/historical_backfill.md](docs/historical_backfill.md) and [docs/examples/historical_backfill_example.csv](docs/examples/historical_backfill_example.csv).

To discover, check, and summarize historical backfill artifacts before larger runs or cache-write approval, use `historical-backfill-index`, `historical-backfill-health`, and `historical-backfill-status`; see [docs/historical_backfill.md#index-health-and-status](docs/historical_backfill.md#index-health-and-status).

`research-status` includes the latest `historical-backfill-status` as a history/cache-building component, while still letting later data-prep, market-update-handoff, current-candidate, or paper workflow artifacts take priority; see [docs/local_research_dashboard.md#historical-backfill-status](docs/local_research_dashboard.md#historical-backfill-status).

For reviewed batch updates, `market-daily-update --symbol-manifest` reads a local CSV symbol list such as [docs/examples/daily_market_symbols_example.csv](docs/examples/daily_market_symbols_example.csv). It is still dry-run-first and not a scheduler.

For deterministic offline batch smoke tests, use a manifest with `raw_input` and `metadata_path` columns such as [docs/examples/daily_market_symbols_offline_example.csv](docs/examples/daily_market_symbols_offline_example.csv). Offline manifests do not need `--allow-real-data`.

For turning accepted reviewed offline update rows into a local snapshot dry-run, use `market-update-handoff`; see [docs/market_update_handoff.md](docs/market_update_handoff.md).

To discover and verify recent reviewed offline update handoffs before paper workflow smoke tests, use `market-update-handoff-index`, `market-update-handoff-health`, and `market-update-handoff-status`; see [docs/market_update_handoff.md#index-health-and-status](docs/market_update_handoff.md#index-health-and-status).

`research-status` includes the latest `market-update-handoff-status` as a pre-paper workflow component, while still letting later paper workflow artifacts take precedence; see [docs/local_research_dashboard.md#market-update-handoff-status](docs/local_research_dashboard.md#market-update-handoff-status).

For comparing overlapping cached market bars across sources such as AKShare and BaoStock, including likely volume/amount unit or source-semantic diagnostics, use `market-cache-compare`; see [docs/market_data_cache.md#compare-sources](docs/market_data_cache.md#compare-sources).

For field-level reliability hints by source, upstream, security type, and market field, use `market-source-policy`; see [docs/market_source_policy.md](docs/market_source_policy.md).

`AKSHARE_OPTIONAL` is available for guarded manual local market, benchmark, trading-calendar, and universe snapshot fetches; it requires `--allow-real-data`, is never called by automated tests, tries non-Eastmoney Sina/Tencent market routes before Eastmoney where supported, includes stock/ETF/index routing diagnostics plus a manual-only `curl_cffi` Eastmoney kline fallback, and should be followed by `data-pipeline`, `data-quality`, and `snapshot-quality`.

`BAOSTOCK_OPTIONAL` is available as a guarded manual market-only historical data backup; it requires `--allow-real-data`, imports BaoStock lazily, is never called by automated tests, writes canonical daily market bars, and can be followed by `market-cache-ingest`, `data-pipeline`, `data-quality`, and `snapshot-quality`.

`TUSHARE_OPTIONAL` is available as a second guarded manual source for market, benchmark, trading-calendar, and universe snapshot fetches; it requires `--allow-real-data` and a local `TUSHARE_TOKEN`, never writes the token to metadata, is never called by automated tests, and should also be followed by `data-pipeline`, `data-quality`, and `snapshot-quality`.

For the guarded Windows CMD workflow from manual AKShare fetch to current candidates, see [docs/akshare_manual_workflow.md](docs/akshare_manual_workflow.md).

For the AKShare universe + market real-data dry-run checklist, see [docs/akshare_real_data_dry_run.md](docs/akshare_real_data_dry_run.md).

For using a manually reviewed market CSV when AKShare market history is unstable, see [docs/local_csv_market_fallback_workflow.md](docs/local_csv_market_fallback_workflow.md).

For merging reviewed ETF rows into a stock-only universe snapshot before `data-pipeline`, see [docs/universe_overlay.md](docs/universe_overlay.md).

For the local data source to ingestion and quality handoff pipeline, see [docs/data_pipeline.md](docs/data_pipeline.md).

For the end-to-end local data preparation smoke-test workflow, see [docs/data_preparation_e2e.md](docs/data_preparation_e2e.md).

For indexing local data preparation artifacts, see [docs/data_preparation_artifact_index.md](docs/data_preparation_artifact_index.md).

For checking indexed data preparation artifact health, see [docs/data_preparation_artifact_health.md](docs/data_preparation_artifact_health.md).

For the local data preparation workflow status dashboard, see [docs/data_preparation_workflow_status.md](docs/data_preparation_workflow_status.md).

For the unified local research workflow dashboard, see [docs/local_research_dashboard.md](docs/local_research_dashboard.md).

For the end-to-end local research workflow smoke-test path, see [docs/local_research_workflow_e2e.md](docs/local_research_workflow_e2e.md).

For the v0.39.0 local research workflow checkpoint summary, see [docs/release_checkpoint_v0.39.0.md](docs/release_checkpoint_v0.39.0.md).

For the v0.64.0 reviewed offline update to `research-status` integration checkpoint summary, see [docs/release_checkpoint_v0.64.0.md](docs/release_checkpoint_v0.64.0.md).

For the v0.67.0 historical backfill status integration checkpoint summary, see [docs/release_checkpoint_v0.67.0.md](docs/release_checkpoint_v0.67.0.md).

For the v0.70.0 reviewed market cache export to `research-status` integration checkpoint summary, see [docs/release_checkpoint_v0.70.0.md](docs/release_checkpoint_v0.70.0.md).

For the v0.71.0 active snapshot warning actionability checkpoint summary, see [docs/release_checkpoint_v0.71.0.md](docs/release_checkpoint_v0.71.0.md).

For the v0.72.0 policy-aware reviewed cache export through `research-status` integration checkpoint summary, see [docs/release_checkpoint_v0.72.0.md](docs/release_checkpoint_v0.72.0.md).

For the v0.73.0 policy-plan source comparison diagnostics through `research-status` integration checkpoint summary, see [docs/release_checkpoint_v0.73.0.md](docs/release_checkpoint_v0.73.0.md).

For the v0.74.0 partial historical backfill cache-write actionability checkpoint summary, see [docs/release_checkpoint_v0.74.0.md](docs/release_checkpoint_v0.74.0.md).

For the v0.75.0 9-symbol policy-aware export to WATCH_ONLY paper workflow validation checkpoint summary, see [docs/release_checkpoint_v0.75.0.md](docs/release_checkpoint_v0.75.0.md).

For the v0.76.0 synthetic fill reconciliation diagnostics and paper workflow status actionability checkpoint summary, see [docs/release_checkpoint_v0.76.0.md](docs/release_checkpoint_v0.76.0.md).

For the v0.77.0 explicit diagnostic reconciliation artifact scope support checkpoint summary, see [docs/release_checkpoint_v0.77.0.md](docs/release_checkpoint_v0.77.0.md).

For the v0.78.0 Signal Advisory Contract and Alert Preview checkpoint summary, see [docs/release_checkpoint_v0.78.0.md](docs/release_checkpoint_v0.78.0.md).

For the v0.80.0 Signal Advisory Artifact Views and Research Status Integration checkpoint summary, see [docs/release_checkpoint_v0.80.0.md](docs/release_checkpoint_v0.80.0.md).

For the v0.81.0 Single-Symbol Advisory Review checkpoint summary, see [docs/release_checkpoint_v0.81.0.md](docs/release_checkpoint_v0.81.0.md).

For the v0.82.0 Single-Symbol Advisory Artifact Views and Research Status Integration checkpoint summary, see [docs/release_checkpoint_v0.82.0.md](docs/release_checkpoint_v0.82.0.md).

For the v0.83.0 Question-style Single-Symbol Advisory Response checkpoint summary, see [docs/release_checkpoint_v0.83.0.md](docs/release_checkpoint_v0.83.0.md).

For the v0.84.0 Question-style Single-Symbol Advisory Answer Artifact Views and Research Status Integration checkpoint summary, see [docs/release_checkpoint_v0.84.0.md](docs/release_checkpoint_v0.84.0.md).

For the v0.85.0 Local-only Conversational Advisory Facade checkpoint summary, see [docs/release_checkpoint_v0.85.0.md](docs/release_checkpoint_v0.85.0.md).

For the v0.86.0 Advisory Conversation Artifact Index / Health / Status checkpoint summary, see [docs/release_checkpoint_v0.86.0.md](docs/release_checkpoint_v0.86.0.md).

For the v0.87.0 Advisory Conversation Research Status Integration checkpoint summary, see [docs/release_checkpoint_v0.87.0.md](docs/release_checkpoint_v0.87.0.md).

For the v0.88.0 Signal Advisory Semantics Policy checkpoint summary, see [docs/release_checkpoint_v0.88.0.md](docs/release_checkpoint_v0.88.0.md).

For the v0.89.0 Signal Semantics Research Status Integration checkpoint summary, see [docs/release_checkpoint_v0.89.0.md](docs/release_checkpoint_v0.89.0.md).

For the v0.90.0 Shared Signal Semantics Wiring Across Advisory Layers checkpoint summary, see [docs/release_checkpoint_v0.90.0.md](docs/release_checkpoint_v0.90.0.md).

For the v0.91.0 Shared Signal Semantics Provenance Metadata checkpoint summary, see [docs/release_checkpoint_v0.91.0.md](docs/release_checkpoint_v0.91.0.md).

For the v0.92.0 Shared Signal Semantics Provenance Visibility checkpoint summary, see [docs/release_checkpoint_v0.92.0.md](docs/release_checkpoint_v0.92.0.md).

For the v0.93.0 Non-Demo Advisory Profile Calibration Analyzer checkpoint summary, see [docs/release_checkpoint_v0.93.0.md](docs/release_checkpoint_v0.93.0.md).

For the v0.94.0 Advisory Profile Calibration Artifact Views and Research Status Integration checkpoint summary, see [docs/release_checkpoint_v0.94.0.md](docs/release_checkpoint_v0.94.0.md).

For the v0.96.0 Calibration-to-Signal-Semantics Research Status Integration checkpoint summary, see [docs/release_checkpoint_v0.96.0.md](docs/release_checkpoint_v0.96.0.md).

For the v0.97.0 Multi-date Current-Candidates Backfill Plan checkpoint summary, see [docs/release_checkpoint_v0.97.0.md](docs/release_checkpoint_v0.97.0.md).

For Codex local CLI verification and artifact diagnostics delegation rules, see [docs/PROCESS.md#codex-local-cli-verification-and-artifact-diagnostics](docs/PROCESS.md#codex-local-cli-verification-and-artifact-diagnostics).

Recommended next data-source engineering sequence:

1. BaoStock local dry-run coverage expansion for more representative stock symbols.
2. Tushare permissioned dry-run if cost and account permissions are acceptable.
3. Professional data adapter evaluation for JQData/RQData if local workflow needs stronger coverage.

```powershell
python -m quant_replay_system.cli data-source-fetch --source LOCAL_CSV --dataset-type market --input data/mock/prices.csv
python -m quant_replay_system.cli data-source-health --source AKSHARE_OPTIONAL --dataset-type market --symbol 510300 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
python -m quant_replay_system.cli data-source-health --source BAOSTOCK_OPTIONAL --dataset-type market --symbol 000001 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
python -m quant_replay_system.cli data-source-fetch --source BAOSTOCK_OPTIONAL --dataset-type market --symbol 000001 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
python -m quant_replay_system.cli market-cache-preflight --input data/raw/AKSHARE_OPTIONAL/market/<run_id>/raw_data.csv --metadata data/raw/AKSHARE_OPTIONAL/market/<run_id>/metadata.json --require-fields close,volume,amount
python -m quant_replay_system.cli market-daily-update --symbol 000001 --start-date 2024-05-20 --end-date 2024-05-20 --source AKSHARE_OPTIONAL --raw-input data/raw/AKSHARE_OPTIONAL/market/<run_id>/raw_data.csv --metadata data/raw/AKSHARE_OPTIONAL/market/<run_id>/metadata.json --dry-run
python -m quant_replay_system.cli market-daily-update --symbol-manifest data/raw/manual_manifests/daily_market_symbols_example.csv --dry-run
python -m quant_replay_system.cli market-daily-update --symbol-manifest data/raw/manual_manifests/daily_market_symbols_offline_example.csv --dry-run
python -m quant_replay_system.cli market-update-handoff --symbol-manifest data/raw/manual_manifests/daily_market_symbols_offline_example.csv --universe data/raw/LOCAL_CSV/universe_overlay/<overlay_id>/raw_data.csv --trading-calendar data/raw/AKSHARE_OPTIONAL/trading_calendar/<run_id>/raw_data.csv --decision-date 2024-05-20 --universe-name etf_core --selection-profile demo --dry-run
python -m quant_replay_system.cli market-update-handoff-index --root outputs/reports/market_update_handoff
python -m quant_replay_system.cli market-update-handoff-health --index outputs/reports/market_update_handoff/index/market_update_handoff_index.csv
python -m quant_replay_system.cli market-update-handoff-status --root outputs/reports/market_update_handoff
python -m quant_replay_system.cli historical-backfill-index --root outputs/reports/historical_backfill
python -m quant_replay_system.cli historical-backfill-health --index outputs/reports/historical_backfill/index/historical_backfill_index.csv
python -m quant_replay_system.cli historical-backfill-status --root outputs/reports/historical_backfill
python -m quant_replay_system.cli market-cache-ingest --input data/raw/AKSHARE_OPTIONAL/market/<run_id>/raw_data.csv --metadata data/raw/AKSHARE_OPTIONAL/market/<run_id>/metadata.json
python -m quant_replay_system.cli market-cache-compare --symbol 000001 --source-a AKSHARE_OPTIONAL --source-b BAOSTOCK_OPTIONAL
python -m quant_replay_system.cli market-cache-query --symbol 510300 --start-date 2024-01-01 --end-date 2024-05-20 --source AKSHARE_OPTIONAL --upstream-source SINA --output data/raw/manual_cache/510300_market.csv
python -m quant_replay_system.cli market-cache-export --manifest data/raw/manual_manifests/reviewed_cache_export_example.csv --build-pipeline-manifest --universe data/raw/LOCAL_CSV/universe_overlay/<overlay_id>/raw_data.csv --trading-calendar data/raw/AKSHARE_OPTIONAL/trading_calendar/<run_id>/raw_data.csv
python -m quant_replay_system.cli market-cache-export-index
python -m quant_replay_system.cli market-cache-export-health
python -m quant_replay_system.cli market-cache-export-status
python -m quant_replay_system.cli universe-overlay --base-universe data/raw/AKSHARE_OPTIONAL/universe/<run_id>/raw_data.csv --overlay data/raw/manual_overlays/etf_universe_overlay.csv
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data/mock/prices.csv
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --candidates outputs/reports/replay_runs/example/candidates.csv
python -m quant_replay_system.cli paper-review-decisions --decisions outputs/reports/paper_trading/daily/example/decisions.csv --updates data/paper/review_updates.csv --health-check --reviewer-id msj
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --reviewed-decisions outputs/reports/paper_trading/reviews/example/reviewed_decisions.csv --fills data/paper/fills.csv
python -m quant_replay_system.cli paper-reconcile-fills --decisions outputs/reports/paper_trading/daily/example/decisions.csv --fills data/paper/fills.csv
python -m quant_replay_system.cli paper-index --root outputs/reports/paper_trading
python -m quant_replay_system.cli paper-health-check --index outputs/reports/paper_trading/index/paper_artifact_index.csv
python -m quant_replay_system.cli paper-workflow-status --root outputs/reports
python -m quant_replay_system.cli ingest-market --input data/raw/market.csv --output-dir data/processed/market
python -m quant_replay_system.cli data-quality --dataset-type market --input data/processed/market/market_cleaned.csv
python -m quant_replay_system.cli snapshot-quality --manifest data/snapshots/example_snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --top 5 --snapshot-manifest data/snapshots/example_snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --top 5 --snapshot-manifest data/snapshots/example_snapshot_manifest.json --selection-profile demo
python -m quant_replay_system.cli current-candidates-index --root outputs/reports/current_candidates
python -m quant_replay_system.cli current-candidates-health --index outputs/reports/current_candidates/index/current_candidate_artifact_index.csv
python -m quant_replay_system.cli current-to-paper --index outputs/reports/current_candidates/index/current_candidate_artifact_index.csv --decision-date 2024-05-20
python -m quant_replay_system.cli current-to-paper-review --handoff-dir outputs/reports/current_to_paper_handoff/example
python -m quant_replay_system.cli paper-review-template-health --updates outputs/reports/current_to_paper_review_handoff/example/review_updates_template.csv --decisions outputs/reports/paper_trading/daily/example/decisions.csv
python -m quant_replay_system.cli data-prep-index --root outputs/reports
python -m quant_replay_system.cli data-prep-health --index outputs/reports/data_preparation/index/data_preparation_artifact_index.csv
python -m quant_replay_system.cli data-prep-status --root outputs/reports
python -m quant_replay_system.cli research-status --root outputs/reports
python -m quant_replay_system.cli replay-run --date 2024-01-03 --horizon 2 --snapshot-manifest data/snapshots/example_snapshot_manifest.json
python -m quant_replay_system.cli batch-replay --dates 2024-01-03,2024-01-04 --horizon 2 --snapshot-manifest data/snapshots/example_snapshot_manifest.json
python -m quant_replay_system.cli paper-validate-fills --fills data/paper/fills.csv
python -m quant_replay_system.cli paper-template-fills --output data/paper/fills_template.csv
```

## Current Candidate To Paper Workflow

```powershell
python -m quant_replay_system.cli data-source-fetch --source LOCAL_CSV --dataset-type market --input data/raw/market.csv
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data/raw/market.csv
python -m quant_replay_system.cli ingest-market --input data/raw/market.csv --output-dir data/processed/market
python -m quant_replay_system.cli snapshot-quality --manifest data/snapshots/example_snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --top 5 --snapshot-manifest data/snapshots/example_snapshot_manifest.json
python -m quant_replay_system.cli current-candidates-index --root outputs/reports/current_candidates
python -m quant_replay_system.cli current-candidates-health --index outputs/reports/current_candidates/index/current_candidate_artifact_index.csv
python -m quant_replay_system.cli current-to-paper --index outputs/reports/current_candidates/index/current_candidate_artifact_index.csv --decision-date 2024-05-20 --universe etf_core
python -m quant_replay_system.cli current-to-paper-review --handoff-dir outputs/reports/current_to_paper_handoff/example --reviewer-id msj
# Manually edit outputs\reports\current_to_paper_review_handoff\example\review_updates_template.csv
python -m quant_replay_system.cli paper-review-template-health --updates outputs/reports/current_to_paper_review_handoff/example/review_updates_template.csv --decisions outputs/reports/paper_trading/daily/example/decisions.csv
python -m quant_replay_system.cli paper-review-decisions --decisions outputs/reports/paper_trading/daily/example/decisions.csv --updates outputs/reports/current_to_paper_review_handoff/example/review_updates_template.csv --health-check --reviewer-id msj
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --reviewed-decisions outputs/reports/paper_trading/reviews/example/reviewed_decisions.csv --fills data/paper/fills.csv
python -m quant_replay_system.cli paper-reconcile-fills --decisions outputs/reports/paper_trading/daily/example/decisions.csv --fills data/paper/fills.csv
python -m quant_replay_system.cli paper-workflow-status --root outputs/reports --decision-date 2024-05-20 --universe etf_core
python -m quant_replay_system.cli research-status --root outputs/reports --decision-date 2024-05-20 --universe etf_core
```

## Local Data Source Workflow

```powershell
python -m quant_replay_system.cli data-source-fetch --source LOCAL_CSV --dataset-type market --input data/mock/prices.csv
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input data/mock/prices.csv
python -m quant_replay_system.cli data-quality --dataset-type market --input data/processed/market/<pipeline_id>/raw_data_cleaned.csv
python -m quant_replay_system.cli snapshot-quality --manifest data/snapshots/example_snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --snapshot-manifest data/snapshots/example_snapshot_manifest.json
```

## Local Data Preparation E2E Workflow

```powershell
python -m quant_replay_system.cli data-pipeline --manifest data/mock/data_pipeline_manifest.json
python -m quant_replay_system.cli data-prep-status --root outputs/reports
python -m quant_replay_system.cli snapshot-quality --manifest outputs/reports/data_pipeline/<pipeline_id>/snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date 2024-01-08 --universe etf_core --top 5 --snapshot-manifest outputs/reports/data_pipeline/<pipeline_id>/snapshot_manifest.json
python -m quant_replay_system.cli data-prep-index --root outputs/reports
python -m quant_replay_system.cli data-prep-health --index outputs/reports/data_preparation/index/data_preparation_artifact_index.csv
python -m quant_replay_system.cli data-prep-status --root outputs/reports --decision-date 2024-01-08 --universe etf_core
python -m quant_replay_system.cli current-to-paper --candidates outputs/reports/current_candidates/<run_folder>/candidates.csv --paper-date 2024-01-08
# Continue with the manual paper workflow: current-to-paper-review, paper-review-decisions, paper-daily, and paper-reconcile-fills.
```

## Data Preparation Status Workflow

```powershell
python -m quant_replay_system.cli data-pipeline --manifest data/mock/data_pipeline_manifest.json
python -m quant_replay_system.cli data-prep-status --root outputs/reports
python -m quant_replay_system.cli snapshot-quality --manifest outputs/reports/data_pipeline/<pipeline_id>/snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date 2024-01-08 --universe etf_core --snapshot-manifest outputs/reports/data_pipeline/<pipeline_id>/snapshot_manifest.json
python -m quant_replay_system.cli current-to-paper --candidates outputs/reports/current_candidates/<run_folder>/candidates.csv --paper-date 2024-01-08
```

## Unified Local Research Workflow

```powershell
python -m quant_replay_system.cli data-pipeline --manifest data/mock/data_pipeline_manifest.json
python -m quant_replay_system.cli data-prep-status --root outputs/reports
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --snapshot-manifest outputs/reports/data_pipeline/<pipeline_id>/snapshot_manifest.json
python -m quant_replay_system.cli current-to-paper --candidates outputs/reports/current_candidates/<run_folder>/candidates.csv --paper-date 2024-05-20
python -m quant_replay_system.cli current-to-paper-review --handoff-dir outputs/reports/current_to_paper_handoff/example
# Manually edit review_updates_template.csv.
python -m quant_replay_system.cli paper-review-decisions --decisions outputs/reports/paper_trading/daily/example/decisions.csv --updates outputs/reports/current_to_paper_review_handoff/example/review_updates_template.csv --health-check
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --reviewed-decisions outputs/reports/paper_trading/reviews/example/reviewed_decisions.csv
python -m quant_replay_system.cli paper-reconcile-fills --decisions outputs/reports/paper_trading/daily/example/decisions.csv --fills data/paper/fills.csv
python -m quant_replay_system.cli research-status --root outputs/reports --decision-date 2024-05-20 --universe etf_core
```

The automated smoke-test version of this flow is documented in [docs/local_research_workflow_e2e.md](docs/local_research_workflow_e2e.md) and covered by `tests/test_local_research_workflow_e2e.py`.

## Local Research Workflow Checkpoint

`v0.39.0` marks the first complete local-only research workflow checkpoint, covering local data preparation, snapshot quality, current candidates, paper review, paper reporting, fill reconciliation, and the unified `research-status` dashboard.

See [docs/release_checkpoint_v0.39.0.md](docs/release_checkpoint_v0.39.0.md) for the milestone summary, local command sequence, safety guarantees, known limitations, and recommended tag.

`v0.64.0` marks the reviewed offline market update to `research-status` integration checkpoint, covering market-cache preflight, offline reviewed symbol manifests, market-update-handoff, handoff index/health/status, current-candidates demo handoff, WATCH_ONLY paper workflow smoke testing, and exported dashboard field regression coverage.

See [docs/release_checkpoint_v0.64.0.md](docs/release_checkpoint_v0.64.0.md) for the milestone summary, safety boundaries, validation baseline, known limitations, and recommended next engineering tasks.

`v0.67.0` marks the historical backfill status integration checkpoint, covering the historical-backfill skeleton, index, health, status, and unified `research-status` dashboard integration while preserving later paper workflow priority.

See [docs/release_checkpoint_v0.67.0.md](docs/release_checkpoint_v0.67.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.70.0` marks the reviewed market cache export to `research-status` integration checkpoint, covering explicit source/upstream cache exports, duplicate-key protection, data-pipeline/data-quality/snapshot-quality validation, export index/health/status, and unified dashboard CSV/metadata regression coverage.

See [docs/release_checkpoint_v0.70.0.md](docs/release_checkpoint_v0.70.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.71.0` marks the active snapshot warning actionability checkpoint, covering active snapshot chain selection in `research-status`, stale/unrelated snapshot warning classification, linked PASS/WARN/FAIL handling, and preservation of paper workflow priority.

See [docs/release_checkpoint_v0.71.0.md](docs/release_checkpoint_v0.71.0.md) for the milestone summary, workflow impact, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.72.0` marks the policy-aware reviewed cache export through `research-status` integration checkpoint, covering policy-based source/upstream recommendations, generated reviewed export manifests, policy-plan index/health/status, reviewed export/snapshot linkage, and dashboard context that preserves later workflow priority.

See [docs/release_checkpoint_v0.72.0.md](docs/release_checkpoint_v0.72.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.73.0` marks the policy-plan source comparison diagnostics through `research-status` integration checkpoint, covering comparison diagnostics in policy-plan recommendations, comparison PASS/WARN/FAIL/UNAVAILABLE summaries, artifact-view health/status integration, and dashboard CSV/metadata/CLI fields that preserve later workflow priority.

See [docs/release_checkpoint_v0.73.0.md](docs/release_checkpoint_v0.73.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.74.0` marks the partial historical backfill cache-write actionability checkpoint, covering protective preflight rejection classification, `BACKFILL_PARTIAL_WITH_REJECTIONS`, rejected row status fields, and `research-status` context that preserves later paper workflow priority.

See [docs/release_checkpoint_v0.74.0.md](docs/release_checkpoint_v0.74.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.75.0` marks the 9-symbol policy-aware export to WATCH_ONLY paper workflow validation checkpoint, covering demo current-candidates artifact handoff, WATCH_ONLY review updates, paper-daily reviewed-decision reporting, zero approvals, zero positions, expected no-fill warnings, and `research-status` preservation of the paper workflow path.

See [docs/release_checkpoint_v0.75.0.md](docs/release_checkpoint_v0.75.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.76.0` marks the synthetic fill reconciliation diagnostics and paper workflow status actionability checkpoint, covering enforced WATCH_ONLY fill rejection, `DECISION_NOT_APPROVED`, diagnostic versus active reconciliation scoping, zero approvals, zero positions, and `research-status` preservation of the active paper workflow.

See [docs/release_checkpoint_v0.76.0.md](docs/release_checkpoint_v0.76.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.77.0` marks the explicit diagnostic reconciliation artifact scope support checkpoint, covering `paper-reconcile-fills --artifact-scope diagnostic`, persisted diagnostic metadata, active versus diagnostic reconciliation behavior, and dashboard preservation of the active WATCH_ONLY/no-fills paper workflow.

See [docs/release_checkpoint_v0.77.0.md](docs/release_checkpoint_v0.77.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.80.0` marks the signal advisory artifact views and `research-status` integration checkpoint, covering advisory index/health/status, dashboard signal context fields, local alert-preview visibility, demo-only actionability, and preservation of later paper workflow priority.

See [docs/release_checkpoint_v0.80.0.md](docs/release_checkpoint_v0.80.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.81.0` marks the Single-Symbol Advisory Review checkpoint, covering focused one-symbol lookup from local artifacts, leading-zero symbol preservation, `DEMO_ONLY` / `NOT_FOUND` / `BLOCKED` / `NO_ACTION` behavior, local alert preview, and manual-confirmation safety flags.

See [docs/release_checkpoint_v0.81.0.md](docs/release_checkpoint_v0.81.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.82.0` marks the single-symbol advisory artifact views and `research-status` integration checkpoint, covering one-symbol advisory index/health/status, dashboard context fields, safe `NOT_FOUND` handling without invented recommendations, demo-only actionability, and preservation of later paper workflow priority.

See [docs/release_checkpoint_v0.82.0.md](docs/release_checkpoint_v0.82.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.83.0` marks the question-style single-symbol advisory response checkpoint, covering deterministic local answers, markdown/json/metadata answer artifacts, demo-only answer safety, safe `NOT_FOUND` behavior, no LLM/API calls, and no message/order execution.

See [docs/release_checkpoint_v0.83.0.md](docs/release_checkpoint_v0.83.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.84.0` marks the question-style single-symbol advisory answer artifact views and `research-status` integration checkpoint, covering answer index/health/status, dashboard answer context fields, demo-only and safe `NOT_FOUND` actionability, no LLM/message/order execution, and preservation of later paper workflow priority.

See [docs/release_checkpoint_v0.84.0.md](docs/release_checkpoint_v0.84.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.85.0` marks the local-only conversational advisory facade checkpoint, covering deterministic Chinese/English question parsing, six-digit symbol extraction, simple intent classification, routing to single-symbol advisory answers, safe `PARSE_FAILED` / `NOT_FOUND` behavior, and no LLM/API/message/order execution.

See [docs/release_checkpoint_v0.85.0.md](docs/release_checkpoint_v0.85.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.86.0` marks the advisory conversation artifact views checkpoint, covering conversation index/health/status, deterministic parsed-question artifact discovery, safety checks for no LLM/API/message/trading behavior, safe `PARSE_FAILED` and `NOT_FOUND` handling, and linked single-symbol answer visibility.

See [docs/release_checkpoint_v0.86.0.md](docs/release_checkpoint_v0.86.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.87.0` marks the advisory conversation `research-status` integration checkpoint, covering dashboard visibility for the latest user question, parsed symbol/intent, conversation status/stage/action, local-only safety flags, linked answer path, safe `PARSE_FAILED` / `NOT_FOUND` context, and preservation of later paper workflow priority.

See [docs/release_checkpoint_v0.87.0.md](docs/release_checkpoint_v0.87.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.88.0` marks the Signal Advisory Semantics Policy checkpoint, covering deterministic advisory label mapping, demo-only safety, structural non-demo review labels, risk/data/snapshot gates, leading-zero symbol preservation, and no-auto-order safety fields.

See [docs/release_checkpoint_v0.88.0.md](docs/release_checkpoint_v0.88.0.md) for the milestone summary, workflow impact, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.89.0` marks the Signal Semantics Research Status Integration checkpoint, covering signal-semantics index/health/status observability, dashboard action-count visibility, human-review-only `REVIEW_BUY_CANDIDATE` semantics, demo-only safety, and preservation of later paper workflow priority.

See [docs/release_checkpoint_v0.89.0.md](docs/release_checkpoint_v0.89.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.90.0` marks the Shared Signal Semantics Wiring Across Advisory Layers checkpoint, covering shared classification across `signal-advisory`, `single-symbol-advisory`, question-style answers, and advisory conversation routing while preserving demo-only, `NOT_FOUND`, `PARSE_FAILED`, blocked-row, manual-confirmation, and no-auto-order safety boundaries.

See [docs/release_checkpoint_v0.90.0.md](docs/release_checkpoint_v0.90.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.91.0` marks the Shared Signal Semantics Provenance Metadata checkpoint, covering provenance fields in downstream advisory artifacts, health checks for missing or unsafe provenance, legacy missing-provenance warnings, and preservation of no-auto-order/no-broker/no-live-trading/no-message safety boundaries.

See [docs/release_checkpoint_v0.91.0.md](docs/release_checkpoint_v0.91.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.92.0` marks the Shared Signal Semantics Provenance Visibility checkpoint, covering provenance visibility in advisory index/status views and unified `research-status`, regenerated provenance-bearing single-symbol artifacts, warning-only legacy provenance context, and preservation of later paper workflow priority.

See [docs/release_checkpoint_v0.92.0.md](docs/release_checkpoint_v0.92.0.md) for the milestone summary, workflow chain, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.93.0` marks the Non-Demo Advisory Profile Calibration Analyzer checkpoint, covering local threshold-analysis profiles, simulated calibration labels, demo-only safety, quality/risk blocking gates, and no-order/no-broker/no-message boundaries before any future non-demo semantics wiring.

See [docs/release_checkpoint_v0.93.0.md](docs/release_checkpoint_v0.93.0.md) for the milestone summary, workflow impact, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.94.0` marks the Advisory Profile Calibration Artifact Views and Research Status Integration checkpoint, covering calibration index/health/status, dashboard calibration context fields, health PASS verification, human-review-only review labels, and preservation of later paper workflow priority.

See [docs/release_checkpoint_v0.94.0.md](docs/release_checkpoint_v0.94.0.md) for the milestone summary, workflow impact, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.96.0` marks the Calibration-to-Signal-Semantics Research Status Integration checkpoint, covering proposal report observability, proposal index/health/status, unified dashboard proposal context fields, `defaults_changed=False` visibility, conservative proposal categories, and preservation of later paper workflow priority.

See [docs/release_checkpoint_v0.96.0.md](docs/release_checkpoint_v0.96.0.md) for the milestone summary, workflow impact, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.97.0` marks the Multi-date Current-Candidates Backfill Plan checkpoint, covering local cache coverage planning, selected feasible signal dates, forward-horizon availability, distinct-symbol coverage under duplicate source rows, reviewed source/upstream guidance, and plan-only safety boundaries before candidate generation.

See [docs/release_checkpoint_v0.97.0.md](docs/release_checkpoint_v0.97.0.md) for the milestone summary, workflow impact, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.98.0` marks the Current-Candidates Backfill Execution Manifest Artifact Views checkpoint, covering execution manifest index/health/status views, readiness and blocker counts, plan-only safety boundaries, and no current-candidates/no snapshot-build/no forward-label behavior.

See [docs/release_checkpoint_v0.98.0.md](docs/release_checkpoint_v0.98.0.md) for the milestone summary, workflow impact, safety boundaries, validation baseline, known limitations, and recommended tag.

`v0.99.0` marks the Current-Candidates Backfill Execution Manifest Research Status Integration checkpoint, covering dashboard visibility for execution manifest readiness, `BLOCKED_UNIVERSE_AS_OF` blockers, linked warmup-aware plan context, manifest-only safety boundaries, and preservation of later paper workflow priority.

See [docs/release_checkpoint_v0.99.0.md](docs/release_checkpoint_v0.99.0.md) for the milestone summary, workflow impact, safety boundaries, validation baseline, known limitations, and recommended tag.

`v1.1.0` marks the Reviewed PIT Universe Overlay Review Artifact Views and Research Status Integration checkpoint, covering reviewed approval artifact index/health/status views, evidence-required approval safety checks, unresolved survivorship warning visibility, dashboard integration, and preservation of later paper workflow priority.

See [docs/release_checkpoint_v1.1.0.md](docs/release_checkpoint_v1.1.0.md) for the milestone summary, workflow impact, safety boundaries, validation baseline, known limitations, and recommended tag.

`v1.9.0` marks the Universe Profile Split-Worklist Plan Artifact Views and Research Status Integration checkpoint, covering split-plan index/health/status views, dashboard visibility for profile conflicts and future universe recommendations, planning-only safety checks, and preservation of later paper workflow priority.

See [docs/release_checkpoint_v1.9.0.md](docs/release_checkpoint_v1.9.0.md) for the milestone summary, workflow impact, safety boundaries, validation baseline, known limitations, and recommended tag.

`v1.10.0` marks the Reviewed Replacement Worklist Planning checkpoint, covering report-only replacement templates for `stock_core`, `etf_core`, and `mixed_demo_core`, replacement-plan index/health/status views, dashboard visibility, and preservation of later paper workflow priority.

See [docs/release_checkpoint_v1.10.0.md](docs/release_checkpoint_v1.10.0.md) for the milestone summary, workflow impact, safety boundaries, validation baseline, known limitations, and recommended tag.

`v1.11.0` marks the Reviewed Replacement Worklist Acceptance checkpoint, covering report-only acknowledgement of replacement templates, acceptance index/health/status views, dashboard visibility, lineage preservation, and preservation of later paper workflow priority.

See [docs/release_checkpoint_v1.11.0.md](docs/release_checkpoint_v1.11.0.md) for the milestone summary, workflow impact, safety boundaries, validation baseline, known limitations, and recommended tag.

See [docs/release_checkpoint_v1.12.0.md](docs/release_checkpoint_v1.12.0.md) for the milestone summary, workflow impact, safety boundaries, validation baseline, known limitations, and recommended tag.

## Project Layout

```text
quant-replay-system/
  config/
    default.yaml
    universe.yaml
  data/
    mock/
      corporate_actions.csv
      data_pipeline_manifest.json
      prices.csv
      trading_calendar.csv
      universe_snapshots.csv
  docs/
    CODEX_PROMPT_STANDARD.md
    akshare_manual_workflow.md
    akshare_real_data_dry_run.md
    batch_replay.md
    current_candidate_artifact_health.md
    current_candidate_artifact_index.md
    current_candidate_generation.md
    current_to_paper_handoff.md
    current_to_paper_review_handoff.md
    data_contract.md
    data_ingestion.md
    data_pipeline.md
    data_preparation_artifact_health.md
    data_preparation_artifact_index.md
    data_preparation_e2e.md
    data_preparation_workflow_status.md
    data_quality.md
    data_sources.md
    daily_paper_trading_runner.md
    execution_calendar.md
    factor_dataset.md
    manual_paper_trading.md
    parameter_calibration.md
    paper_fill_reconciliation.md
    paper_review_template_health.md
    paper_trading_artifact_health_check.md
    paper_trading_artifact_index.md
    paper_trading_e2e_workflow.md
    paper_trading_workflow_status.md
    paper_trading_cli.md
    paper_trading_review_workflow.md
    portfolio_aware_calibration.md
    portfolio_simulation.md
    report_generation.md
    replay_run_orchestrator.md
    scoring_engine.md
    snapshot_quality_gate.md
    snapshot_quality_preflight.md
    snapshot_quality_preflight_cli.md
    technical_indicators.md
    testing_strategy.md
    walk_forward_validation.md
  src/
    quant_replay_system/
      calibration.py
      cli.py
      config.py
      current_candidate_artifact_health.py
      current_candidate_artifact_index.py
      current_candidates.py
      current_to_paper_handoff.py
      current_to_paper_review_handoff.py
      data.py
      data_ingestion.py
      data_pipeline.py
      data_preparation_artifact_health.py
      data_preparation_artifact_index.py
      data_preparation_workflow_status.py
      data_quality.py
      data_sources.py
      daily_paper_runner.py
      evaluation.py
      execution.py
      paper_artifact_health.py
      paper_artifact_index.py
      paper_reconciliation.py
      paper_review.py
      paper_trading.py
      replay.py
      risk.py
      scoring.py
      snapshot_quality_gate.py
      snapshot_quality_preflight.py
      walk_forward.py
  tests/
```

## Design Principles

- Point-in-time safety first.
- Explainable scores before complex models.
- T+1 execution assumptions are explicit.
- Local files and mock data are the default for MVP.
- Paper trading and small manual live workflows can be added later, without broker automation.

## Example Baseline Flow

```python
from pathlib import Path

from quant_replay_system.config import load_settings
from quant_replay_system.calendar import load_trading_calendar
from quant_replay_system.data import load_corporate_actions, load_market_data, load_universe_snapshot
from quant_replay_system.replay import replay_decision_date

settings = load_settings(Path("config/default.yaml"))
prices = load_market_data(settings.data.mock_prices)
universe = load_universe_snapshot(settings.data.mock_universe_snapshots)
actions = load_corporate_actions(settings.data.mock_corporate_actions)
calendar = load_trading_calendar(settings.data.mock_trading_calendar)
result = replay_decision_date("2024-01-03", prices, settings, universe, actions, calendar)

print(result.candidates)
```
