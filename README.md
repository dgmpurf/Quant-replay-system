# quant-replay-system

A point-in-time historical replay quant research system for China A-share ETFs and stocks.

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

For local CSV ingestion, validation, and processed snapshot manifests, see [docs/data_ingestion.md](docs/data_ingestion.md).

For processed data quality summaries before replay, see [docs/data_quality.md](docs/data_quality.md).

For full-snapshot PASS/WARN/FAIL quality gates before replay, see [docs/snapshot_quality_gate.md](docs/snapshot_quality_gate.md).

For optional snapshot quality preflight checks inside replay, batch, calibration, and walk-forward flows, see [docs/snapshot_quality_preflight.md](docs/snapshot_quality_preflight.md).

For CLI flags that enable snapshot preflight on replay-like workflows, see [docs/snapshot_quality_preflight_cli.md](docs/snapshot_quality_preflight_cli.md).

For current/as-of-date candidate generation from local snapshots, see [docs/current_candidate_generation.md](docs/current_candidate_generation.md).

`current-candidates --selection-profile demo` is available for tiny local artifact/workflow validation only. The default selection profile and research thresholds remain unchanged, and demo candidates are marked as not strategy recommendations.

For turning current-candidates artifacts into local advisory signals and alert previews without message delivery or execution, see [docs/signal_advisory.md](docs/signal_advisory.md).

For the deterministic policy that maps candidate/scored rows into safe advisory labels such as `DEMO_ONLY`, `WATCH`, and `REVIEW_BUY_CANDIDATE`, see [docs/signal_semantics.md](docs/signal_semantics.md). Demo rows remain workflow validation only, and all labels require manual confirmation with auto-order disabled.

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
