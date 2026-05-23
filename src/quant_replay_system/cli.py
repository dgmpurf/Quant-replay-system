"""Command line helpers for local-only paper trading workflows."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd

from quant_replay_system.batch_replay import run_batch_replay
from quant_replay_system.calibration import run_parameter_calibration
from quant_replay_system.config import load_settings
from quant_replay_system.current_candidate_artifact_health import check_current_candidate_artifact_health
from quant_replay_system.current_candidate_artifact_index import build_current_candidate_artifact_index
from quant_replay_system.current_candidates import generate_current_candidates
from quant_replay_system.current_to_paper_handoff import run_current_to_paper_handoff
from quant_replay_system.current_to_paper_review_handoff import run_current_to_paper_review_handoff
from quant_replay_system.data_preparation_artifact_health import check_data_preparation_artifact_health
from quant_replay_system.data_preparation_artifact_index import build_data_preparation_artifact_index
from quant_replay_system.data_preparation_workflow_status import run_data_preparation_workflow_status
from quant_replay_system.data_pipeline import (
    load_data_pipeline_manifest,
    run_data_source_ingestion_pipeline,
)
from quant_replay_system.data_quality import run_data_quality_checks
from quant_replay_system.data_source_health import run_data_source_health_check
from quant_replay_system.data_sources import DataSourceRequest, run_data_source_fetch
from quant_replay_system.data_ingestion import (
    ingest_benchmark_data_csv,
    ingest_corporate_actions_csv,
    ingest_market_data_csv,
    ingest_trading_calendar_csv,
    ingest_universe_snapshot_csv,
)
from quant_replay_system.daily_paper_runner import run_daily_paper_trading
from quant_replay_system.local_research_dashboard import run_local_research_dashboard
from quant_replay_system.market_data_cache import (
    ingest_market_cache_csv,
    query_market_cache,
    summarize_market_cache_status,
)
from quant_replay_system.paper_artifact_health import check_paper_artifact_health
from quant_replay_system.paper_artifact_index import build_paper_artifact_index
from quant_replay_system.paper_reconciliation import reconcile_paper_fills
from quant_replay_system.paper_review import apply_paper_review_updates
from quant_replay_system.paper_review_template_health import check_review_template_health
from quant_replay_system.paper_workflow_status import run_paper_workflow_status
from quant_replay_system.replay_run import run_replay
from quant_replay_system.snapshot_quality_gate import run_snapshot_quality_gate
from quant_replay_system.snapshot_quality_preflight import SnapshotQualityPreflightError
from quant_replay_system.universe_overlay import run_universe_overlay
from quant_replay_system.walk_forward import run_walk_forward_validation


FILL_COLUMNS = [
    "fill_id",
    "decision_id",
    "symbol",
    "side",
    "fill_date",
    "fill_price",
    "quantity",
    "gross_notional",
    "fees",
    "slippage",
    "net_cash_flow",
    "fill_source",
    "manual_notes",
]

REQUIRED_FILL_COLUMNS = ["decision_id", "symbol", "side", "fill_date", "fill_price", "quantity"]
VALID_FILL_SIDES = {"BUY", "SELL"}


@dataclass(frozen=True)
class FillValidationResult:
    valid: bool
    row_count: int
    errors: list[str]
    warnings: list[str]


def main(argv: Sequence[str] | None = None) -> int:
    """Run the quant replay CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argparse parser."""

    parser = argparse.ArgumentParser(prog="python -m quant_replay_system.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    replay = subparsers.add_parser(
        "replay-run",
        aliases=["replay"],
        help="Run a local single-date replay workflow",
    )
    replay.add_argument("--date", required=True, help="Decision date, e.g. 2024-01-03")
    replay.add_argument("--universe", default="default", help="Universe name")
    replay.add_argument("--top", type=int, help="Candidate count override")
    replay.add_argument("--horizon", type=int, help="Holding horizon in trading days")
    replay.add_argument("--output-dir", help="Optional replay output directory")
    replay.add_argument("--config", help="Optional config YAML path")
    _add_snapshot_preflight_arguments(replay)
    replay.set_defaults(handler=_handle_replay_run)

    batch = subparsers.add_parser("batch-replay", help="Run local batch replay over decision dates")
    batch.add_argument("--dates", nargs="+", required=True, help="Decision dates, comma-separated or space-separated")
    batch.add_argument("--universe", default="default", help="Universe name")
    batch.add_argument("--top", type=int, help="Candidate count override")
    batch.add_argument("--horizon", type=int, help="Holding horizon in trading days")
    batch.add_argument("--output-dir", help="Optional batch replay output directory")
    batch.add_argument("--config", help="Optional config YAML path")
    _add_snapshot_preflight_arguments(batch)
    batch.set_defaults(handler=_handle_batch_replay)

    calibrate = subparsers.add_parser(
        "parameter-calibration",
        aliases=["calibrate"],
        help="Run local parameter calibration over decision dates",
    )
    calibrate.add_argument("--dates", nargs="+", required=True, help="Decision dates, comma-separated or space-separated")
    calibrate.add_argument("--universe", default="default", help="Universe name")
    calibrate.add_argument("--output-dir", help="Optional calibration output directory")
    calibrate.add_argument("--config", help="Optional config YAML path")
    _add_snapshot_preflight_arguments(calibrate)
    calibrate.set_defaults(handler=_handle_parameter_calibration)

    walk_forward = subparsers.add_parser("walk-forward", help="Run local walk-forward validation")
    walk_forward.add_argument("--train-dates", nargs="+", required=True, help="Train dates, comma-separated or space-separated")
    walk_forward.add_argument("--validation-dates", nargs="+", required=True, help="Validation dates, comma-separated or space-separated")
    walk_forward.add_argument("--test-dates", nargs="*", default=[], help="Optional test dates, comma-separated or space-separated")
    walk_forward.add_argument("--universe", default="default", help="Universe name")
    walk_forward.add_argument("--output-dir", help="Optional walk-forward output directory")
    walk_forward.add_argument("--config", help="Optional config YAML path")
    _add_snapshot_preflight_arguments(walk_forward)
    walk_forward.set_defaults(handler=_handle_walk_forward)

    current_candidates = subparsers.add_parser(
        "current-candidates",
        help="Generate local current/as-of-date candidates from point-in-time data",
    )
    current_candidates.add_argument("--date", required=True, help="Decision date, e.g. 2024-05-20")
    current_candidates.add_argument("--universe", required=True, help="Universe name")
    current_candidates.add_argument("--top", type=int, help="Candidate count override")
    current_candidates.add_argument("--output-dir", help="Optional current-candidate output directory")
    current_candidates.add_argument(
        "--selection-profile",
        choices=["default", "demo"],
        default="default",
        help="Current-candidate selection profile. Use demo only for local artifact/workflow validation.",
    )
    current_candidates.add_argument("--config", help="Optional config YAML path")
    _add_snapshot_preflight_arguments(current_candidates)
    current_candidates.set_defaults(handler=_handle_current_candidates)

    current_index = subparsers.add_parser(
        "current-candidates-index",
        help="Build a local index of current-candidate artifact folders",
    )
    current_index.add_argument("--root", help="Current-candidate artifact root directory")
    current_index.add_argument("--output-dir", help="Optional index output directory")
    current_index.add_argument("--include-missing-metadata", action="store_true", help="Index folders missing metadata.json")
    current_index.add_argument("--config", help="Optional config YAML path")
    current_index.set_defaults(handler=_handle_current_candidates_index)

    current_health = subparsers.add_parser(
        "current-candidates-health",
        help="Check local current-candidate artifact file health",
    )
    current_health.add_argument("--index", help="Current-candidate artifact index CSV path")
    current_health.add_argument("--root", help="Current-candidate artifact root directory")
    current_health.add_argument("--output-dir", help="Optional health-check output directory")
    current_health.add_argument("--strict", action="store_true", help="Escalate configurable warnings to errors")
    current_health.add_argument("--allow-warn", action="store_true", help="Exit zero when status is WARN in strict mode")
    current_health.add_argument("--config", help="Optional config YAML path")
    current_health.set_defaults(handler=_handle_current_candidates_health)

    current_to_paper = subparsers.add_parser(
        "current-to-paper",
        help="Select a current-candidate artifact and launch local daily paper trading",
    )
    current_to_paper.add_argument("--index", help="Current-candidate artifact index CSV path")
    current_to_paper.add_argument("--root", help="Current-candidate artifact root directory")
    current_to_paper.add_argument("--candidates", help="Explicit candidates.csv path")
    current_to_paper.add_argument("--decision-date", help="Filter current-candidate artifacts by decision date")
    current_to_paper.add_argument("--paper-date", help="Paper trading date. Defaults to selected decision date.")
    current_to_paper.add_argument("--universe", help="Filter current-candidate artifacts by universe name")
    current_to_paper.add_argument("--run-id", help="Filter current-candidate artifacts by run id")
    current_to_paper.add_argument("--fills", help="Optional manual paper fills CSV path")
    current_to_paper.add_argument("--output-dir", help="Optional handoff output directory")
    current_to_paper.add_argument("--journal-id", help="Optional explicit daily paper journal id")
    current_to_paper.add_argument("--allow-health-warn", action="store_true", help="Allow WARN health status artifacts")
    current_to_paper.add_argument("--skip-health-check", action="store_true", help="Skip current-candidate artifact health check")
    current_to_paper.add_argument("--config", help="Optional config YAML path")
    current_to_paper.set_defaults(handler=_handle_current_to_paper)

    current_to_paper_review = subparsers.add_parser(
        "current-to-paper-review",
        help="Create a manual paper review update template from paper decisions",
    )
    current_to_paper_review.add_argument("--decisions", help="Paper decisions CSV path")
    current_to_paper_review.add_argument("--handoff-dir", help="Current-to-paper or daily paper artifact directory")
    current_to_paper_review.add_argument("--output-dir", help="Optional review handoff output directory")
    current_to_paper_review.add_argument("--reviewer-id", help="Default reviewer id for template rows")
    current_to_paper_review.add_argument("--config", help="Optional config YAML path")
    current_to_paper_review.set_defaults(handler=_handle_current_to_paper_review)

    daily = subparsers.add_parser("paper-daily", help="Write a local daily paper trading report")
    daily.add_argument("--date", required=True, help="Paper trading date, e.g. 2024-05-20")
    daily.add_argument("--candidates", help="Candidates CSV path")
    daily.add_argument("--reviewed-decisions", help="Reviewed decisions CSV path")
    daily.add_argument("--fills", help="Optional manual paper fills CSV path")
    daily.add_argument("--mark-prices", help="Optional mark-to-market price CSV path")
    daily.add_argument("--output-dir", help="Optional output directory")
    daily.add_argument("--journal-id", help="Optional explicit journal id")
    daily.add_argument("--config", help="Optional config YAML path")
    daily.set_defaults(handler=_handle_paper_daily)

    validate = subparsers.add_parser("paper-validate-fills", help="Validate a manual fills CSV")
    validate.add_argument("--fills", required=True, help="Manual fills CSV path")
    validate.set_defaults(handler=_handle_validate_fills)

    template = subparsers.add_parser("paper-template-fills", help="Write an empty fills CSV template")
    template.add_argument("--output", required=True, help="Output CSV path")
    template.add_argument("--overwrite", action="store_true", help="Overwrite an existing template")
    template.set_defaults(handler=_handle_template_fills)

    reconcile = subparsers.add_parser("paper-reconcile-fills", help="Reconcile manual fills against decisions")
    reconcile.add_argument("--decisions", required=True, help="Paper decisions CSV path")
    reconcile.add_argument("--fills", required=True, help="Manual fills CSV path")
    reconcile.add_argument("--output-dir", help="Optional reconciliation output directory")
    reconcile.add_argument("--config", help="Optional config YAML path")
    reconcile.add_argument("--allow-fail", action="store_true", help="Exit zero even when reconciliation status is FAIL")
    reconcile.set_defaults(handler=_handle_reconcile_fills)

    review = subparsers.add_parser("paper-review-decisions", help="Apply manual review updates to paper decisions")
    review.add_argument("--decisions", required=True, help="Paper decisions CSV path")
    review.add_argument("--updates", required=True, help="Review updates CSV path")
    review.add_argument("--output-dir", help="Optional review artifact output directory")
    review.add_argument("--reviewer-id", help="Default reviewer id for updates without reviewer_id")
    review.add_argument("--allow-pending", action="store_true", help="Allow reviewed decisions to remain PENDING_REVIEW")
    review.add_argument("--health-check", action="store_true", help="Run review template health check before applying updates")
    review.add_argument("--require-template-health-pass", action="store_true", help="Require template health status PASS before applying updates")
    review.add_argument("--allow-template-health-warn", action="store_true", help="Allow review updates when template health status is WARN")
    review.add_argument("--template-health-output-dir", help="Optional review template health output directory")
    review.add_argument("--config", help="Optional config YAML path")
    review.set_defaults(handler=_handle_review_decisions)

    review_health = subparsers.add_parser(
        "paper-review-template-health",
        help="Health check an edited paper review update template before applying it",
    )
    review_health.add_argument("--updates", required=True, help="Review updates template CSV path")
    review_health.add_argument("--decisions", help="Optional matching paper decisions CSV path")
    review_health.add_argument("--output-dir", help="Optional review template health output directory")
    review_health.add_argument("--strict", action="store_true", help="Escalate configurable warnings to errors")
    review_health.add_argument("--allow-warn", action="store_true", help="Exit zero when status is WARN in strict mode")
    review_health.add_argument("--config", help="Optional config YAML path")
    review_health.set_defaults(handler=_handle_review_template_health)

    index = subparsers.add_parser("paper-index", help="Build a local paper trading artifact index")
    index.add_argument("--root", help="Paper trading artifact root directory")
    index.add_argument("--output-dir", help="Optional index output directory")
    index.add_argument("--include-missing-metadata", action="store_true", help="Index folders missing metadata.json")
    index.add_argument(
        "--artifact-type",
        choices=["daily", "review", "reconciliation", "all"],
        default="all",
        help="Artifact type to index",
    )
    index.add_argument("--config", help="Optional config YAML path")
    index.set_defaults(handler=_handle_paper_index)

    health = subparsers.add_parser("paper-health-check", help="Check local paper artifact file health")
    health.add_argument("--index", help="Paper artifact index CSV path")
    health.add_argument("--root", help="Paper trading artifact root directory")
    health.add_argument("--output-dir", help="Optional health-check output directory")
    health.add_argument("--strict", action="store_true", help="Escalate configurable warnings to errors")
    health.add_argument("--allow-warn", action="store_true", help="Exit zero when status is WARN in strict mode")
    health.add_argument("--config", help="Optional config YAML path")
    health.set_defaults(handler=_handle_paper_health_check)

    workflow_status = subparsers.add_parser(
        "paper-workflow-status",
        help="Build a local paper trading workflow status dashboard",
    )
    workflow_status.add_argument("--root", help="Reports root directory")
    workflow_status.add_argument("--current-candidates-root", help="Current-candidates artifact root directory")
    workflow_status.add_argument("--paper-trading-root", help="Paper trading artifact root directory")
    workflow_status.add_argument("--decision-date", help="Optional decision date filter")
    workflow_status.add_argument("--universe", help="Optional universe name filter")
    workflow_status.add_argument("--output-dir", help="Optional workflow status output directory")
    workflow_status.add_argument("--strict", action="store_true", help="Exit non-zero when workflow status is WARN")
    workflow_status.add_argument("--config", help="Optional config YAML path")
    workflow_status.set_defaults(handler=_handle_paper_workflow_status)

    research_status = subparsers.add_parser(
        "research-status",
        help="Build a unified local research workflow dashboard",
    )
    research_status.add_argument("--root", help="Reports root directory")
    research_status.add_argument("--data-preparation-root", help="Data preparation artifact root directory")
    research_status.add_argument("--current-candidates-root", help="Current-candidates artifact root directory")
    research_status.add_argument("--paper-trading-root", help="Paper trading artifact root directory")
    research_status.add_argument("--decision-date", help="Optional decision date filter")
    research_status.add_argument("--universe", help="Optional universe name filter")
    research_status.add_argument("--output-dir", help="Optional unified dashboard output directory")
    research_status.add_argument("--strict", action="store_true", help="Exit non-zero when dashboard status is WARN")
    research_status.add_argument("--config", help="Optional config YAML path")
    research_status.set_defaults(handler=_handle_research_status)

    data_source = subparsers.add_parser("data-source-fetch", help="Fetch or load raw local market data source files")
    data_source.add_argument("--source", required=True, help="Data source adapter, e.g. LOCAL_CSV, MOCK, AKSHARE_OPTIONAL, TUSHARE_OPTIONAL")
    data_source.add_argument("--dataset-type", required=True, help="Dataset type: market, universe, benchmark, corporate_actions, trading_calendar")
    data_source.add_argument("--input", help="Input CSV path for LOCAL_CSV")
    data_source.add_argument("--output-dir", help="Optional raw output root directory")
    data_source.add_argument("--revision-id", help="Revision id for raw artifacts")
    data_source.add_argument("--allow-real-data", action="store_true", help="Explicit manual opt-in for real/network data adapters")
    data_source.add_argument("--symbol", help="Optional symbol for future real-data adapters")
    data_source.add_argument("--start-date", help="Optional start date for future real-data adapters")
    data_source.add_argument("--end-date", help="Optional end date for future real-data adapters")
    data_source.add_argument("--as-of-date", help="Optional universe snapshot as-of date for real-data adapters")
    data_source.add_argument("--market-type", help="Optional universe market type, e.g. stock, etf, or all")
    data_source.add_argument("--config", help="Optional config YAML path")
    data_source.set_defaults(handler=_handle_data_source_fetch)

    data_source_health = subparsers.add_parser(
        "data-source-health",
        help="Check local data source availability and fallback route health",
    )
    data_source_health.add_argument(
        "--source",
        required=True,
        help="Data source adapter, e.g. LOCAL_CSV, MOCK, AKSHARE_OPTIONAL",
    )
    data_source_health.add_argument(
        "--dataset-type",
        required=True,
        help="Dataset type, e.g. market, universe, benchmark, or trading_calendar",
    )
    data_source_health.add_argument("--input", help="Input CSV path for LOCAL_CSV")
    data_source_health.add_argument("--symbol", help="Market symbol for real-data route checks")
    data_source_health.add_argument("--start-date", help="Optional start date for real-data route checks")
    data_source_health.add_argument("--end-date", help="Optional end date for real-data route checks")
    data_source_health.add_argument("--as-of-date", help="Optional as-of date for snapshot-like checks")
    data_source_health.add_argument("--market-type", help="Optional market type for universe-like checks")
    data_source_health.add_argument(
        "--requested-upstream",
        choices=["TENCENT", "SINA", "EASTMONEY"],
        help="Optional single AKShare upstream route to probe",
    )
    data_source_health.add_argument(
        "--allow-real-data",
        action="store_true",
        help="Explicit manual opt-in for real/network data health checks",
    )
    data_source_health.add_argument("--output-dir", help="Optional health artifact output directory")
    data_source_health.add_argument("--config", help="Optional config YAML path")
    data_source_health.set_defaults(handler=_handle_data_source_health)

    market_cache_ingest = subparsers.add_parser(
        "market-cache-ingest",
        help="Ingest canonical daily market bars into the local market data cache",
    )
    market_cache_ingest.add_argument("--input", required=True, help="Canonical market raw_data.csv path")
    market_cache_ingest.add_argument("--metadata", help="Optional data-source metadata.json path")
    market_cache_ingest.add_argument("--cache-path", help="Optional market cache CSV path")
    market_cache_ingest.add_argument("--output-dir", help="Optional market cache report output directory")
    market_cache_ingest.add_argument("--config", help="Optional config YAML path")
    market_cache_ingest.set_defaults(handler=_handle_market_cache_ingest)

    market_cache_query = subparsers.add_parser(
        "market-cache-query",
        help="Query local cached daily market bars",
    )
    market_cache_query.add_argument("--symbol", required=True, help="Symbol to query, e.g. 510300")
    market_cache_query.add_argument("--start-date", help="Optional inclusive start date")
    market_cache_query.add_argument("--end-date", help="Optional inclusive end date")
    market_cache_query.add_argument("--cache-path", help="Optional market cache CSV path")
    market_cache_query.add_argument("--output", help="Optional output CSV path for query rows")
    market_cache_query.add_argument("--config", help="Optional config YAML path")
    market_cache_query.set_defaults(handler=_handle_market_cache_query)

    market_cache_status = subparsers.add_parser(
        "market-cache-status",
        help="Summarize the local market data cache",
    )
    market_cache_status.add_argument("--cache-path", help="Optional market cache CSV path")
    market_cache_status.add_argument("--output-dir", help="Optional market cache report output directory")
    market_cache_status.add_argument("--config", help="Optional config YAML path")
    market_cache_status.set_defaults(handler=_handle_market_cache_status)

    universe_overlay = subparsers.add_parser(
        "universe-overlay",
        help="Merge reviewed ETF universe overlay rows into a local universe snapshot",
    )
    universe_overlay.add_argument("--base-universe", required=True, help="Base canonical universe CSV path")
    universe_overlay.add_argument("--overlay", required=True, help="Reviewed ETF overlay CSV path")
    universe_overlay.add_argument("--output-dir", help="Optional universe overlay raw output root")
    universe_overlay.add_argument(
        "--allow-override-existing",
        action="store_true",
        help="Allow reviewed overlay rows to replace existing base universe symbols",
    )
    universe_overlay.add_argument("--config", help="Optional config YAML path")
    universe_overlay.set_defaults(handler=_handle_universe_overlay)

    data_pipeline = subparsers.add_parser("data-pipeline", help="Run local data source -> ingestion -> quality pipeline")
    data_pipeline.add_argument("--dataset-type", help="Dataset type for single dataset mode")
    data_pipeline.add_argument("--source", help="Data source adapter for single dataset mode")
    data_pipeline.add_argument("--input", help="Input CSV path for single dataset LOCAL_CSV mode")
    data_pipeline.add_argument("--manifest", help="Local JSON manifest for multi-dataset mode")
    data_pipeline.add_argument("--output-dir", help="Optional pipeline report output directory")
    data_pipeline.add_argument("--skip-data-quality", action="store_true", help="Skip data quality checks")
    data_pipeline.add_argument("--skip-snapshot-manifest", action="store_true", help="Skip snapshot manifest generation")
    data_pipeline.add_argument("--allow-real-data", action="store_true", help="Explicit manual opt-in for real/network data adapters")
    data_pipeline.add_argument("--symbol", help="Optional symbol for single dataset real-data mode")
    data_pipeline.add_argument("--start-date", help="Optional start date for single dataset real-data mode")
    data_pipeline.add_argument("--end-date", help="Optional end date for single dataset real-data mode")
    data_pipeline.add_argument("--as-of-date", help="Optional universe snapshot as-of date for single dataset real-data mode")
    data_pipeline.add_argument("--market-type", help="Optional universe market type for single dataset real-data mode")
    data_pipeline.add_argument("--config", help="Optional config YAML path")
    data_pipeline.set_defaults(handler=_handle_data_pipeline)

    data_prep_index = subparsers.add_parser(
        "data-prep-index",
        help="Build a local index of data preparation artifacts",
    )
    data_prep_index.add_argument("--root", help="Reports root directory")
    data_prep_index.add_argument("--output-dir", help="Optional index output directory")
    data_prep_index.add_argument("--include-missing-metadata", action="store_true", help="Index folders missing metadata.json")
    data_prep_index.add_argument(
        "--artifact-type",
        choices=["data_pipeline", "data_quality", "snapshot_quality", "current_candidates", "all"],
        default="all",
        help="Data preparation artifact type to index",
    )
    data_prep_index.add_argument("--config", help="Optional config YAML path")
    data_prep_index.set_defaults(handler=_handle_data_prep_index)

    data_prep_health = subparsers.add_parser(
        "data-prep-health",
        help="Check indexed local data preparation artifact health",
    )
    data_prep_health.add_argument("--index", help="Data preparation artifact index CSV path")
    data_prep_health.add_argument("--root", help="Reports root directory to scan if no index is provided")
    data_prep_health.add_argument("--output-dir", help="Optional health-check output directory")
    data_prep_health.add_argument("--strict", action="store_true", help="Escalate configurable warnings to errors")
    data_prep_health.add_argument("--allow-warn", action="store_true", help="Exit zero when status is WARN in strict mode")
    data_prep_health.add_argument("--config", help="Optional config YAML path")
    data_prep_health.set_defaults(handler=_handle_data_prep_health)

    data_prep_status = subparsers.add_parser(
        "data-prep-status",
        help="Build a local data preparation workflow status dashboard",
    )
    data_prep_status.add_argument("--root", help="Reports root directory")
    data_prep_status.add_argument("--data-pipeline-root", help="Data pipeline artifact root directory")
    data_prep_status.add_argument("--data-quality-root", help="Data quality artifact root directory")
    data_prep_status.add_argument("--snapshot-quality-root", help="Snapshot quality artifact root directory")
    data_prep_status.add_argument("--current-candidates-root", help="Current-candidates artifact root directory")
    data_prep_status.add_argument("--decision-date", help="Optional current-candidate decision date filter")
    data_prep_status.add_argument("--universe", help="Optional current-candidate universe filter")
    data_prep_status.add_argument("--output-dir", help="Optional workflow status output directory")
    data_prep_status.add_argument("--strict", action="store_true", help="Exit non-zero when workflow status is WARN")
    data_prep_status.add_argument("--config", help="Optional config YAML path")
    data_prep_status.set_defaults(handler=_handle_data_prep_status)

    ingest_market = subparsers.add_parser("ingest-market", help="Ingest local market daily CSV")
    ingest_market.add_argument("--input", required=True, help="Input market CSV path")
    ingest_market.add_argument("--output-dir", help="Optional processed market output directory")
    ingest_market.add_argument("--config", help="Optional config YAML path")
    ingest_market.set_defaults(handler=_handle_ingest_market)

    ingest_universe = subparsers.add_parser("ingest-universe", help="Ingest local universe snapshot CSV")
    ingest_universe.add_argument("--input", required=True, help="Input universe CSV path")
    ingest_universe.add_argument("--output-dir", help="Optional processed universe output directory")
    ingest_universe.add_argument("--config", help="Optional config YAML path")
    ingest_universe.set_defaults(handler=_handle_ingest_universe)

    ingest_benchmark = subparsers.add_parser("ingest-benchmark", help="Ingest local benchmark daily CSV")
    ingest_benchmark.add_argument("--input", required=True, help="Input benchmark CSV path")
    ingest_benchmark.add_argument("--output-dir", help="Optional processed benchmark output directory")
    ingest_benchmark.add_argument("--config", help="Optional config YAML path")
    ingest_benchmark.set_defaults(handler=_handle_ingest_benchmark)

    ingest_actions = subparsers.add_parser("ingest-corporate-actions", help="Ingest local corporate actions CSV")
    ingest_actions.add_argument("--input", required=True, help="Input corporate actions CSV path")
    ingest_actions.add_argument("--output-dir", help="Optional processed corporate actions output directory")
    ingest_actions.add_argument("--config", help="Optional config YAML path")
    ingest_actions.set_defaults(handler=_handle_ingest_corporate_actions)

    ingest_calendar = subparsers.add_parser("ingest-calendar", help="Ingest local trading calendar CSV")
    ingest_calendar.add_argument("--input", required=True, help="Input trading calendar CSV path")
    ingest_calendar.add_argument("--output-dir", help="Optional processed calendar output directory")
    ingest_calendar.add_argument("--config", help="Optional config YAML path")
    ingest_calendar.set_defaults(handler=_handle_ingest_calendar)

    quality = subparsers.add_parser("data-quality", help="Run local data quality checks")
    quality.add_argument("--dataset-type", required=True, help="Dataset type: market, universe, benchmark, corporate_actions, trading_calendar")
    quality.add_argument("--input", required=True, help="Input canonical/processed CSV path")
    quality.add_argument("--output-dir", help="Optional data quality output directory")
    quality.add_argument("--strict", action="store_true", help="Escalate configurable warnings to errors")
    quality.add_argument("--config", help="Optional config YAML path")
    quality.set_defaults(handler=_handle_data_quality)

    snapshot_quality = subparsers.add_parser("snapshot-quality", help="Run snapshot-level data quality gate")
    snapshot_quality.add_argument("--manifest", required=True, help="Snapshot manifest JSON path")
    snapshot_quality.add_argument("--output-dir", help="Optional snapshot quality output directory")
    snapshot_quality.add_argument("--strict", action="store_true", help="Exit non-zero on WARN and escalate required warnings")
    snapshot_quality.add_argument("--allow-warn", action="store_true", help="Exit zero when status is WARN")
    snapshot_quality.add_argument("--config", help="Optional config YAML path")
    snapshot_quality.set_defaults(handler=_handle_snapshot_quality)
    return parser


def validate_fills_csv(path: str | Path) -> FillValidationResult:
    """Validate a manual paper fills CSV."""

    csv_path = Path(path)
    if not csv_path.exists():
        return FillValidationResult(False, 0, [f"Fills file not found: {csv_path}"], [])
    try:
        frame = pd.read_csv(csv_path)
    except Exception as exc:
        return FillValidationResult(False, 0, [f"Could not read fills CSV: {exc}"], [])
    return validate_fills_frame(frame)


def validate_fills_frame(frame: pd.DataFrame) -> FillValidationResult:
    """Validate the expected manual paper fills schema and values."""

    errors: list[str] = []
    warnings: list[str] = []
    missing = [column for column in REQUIRED_FILL_COLUMNS if column not in frame.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return FillValidationResult(False, len(frame), errors, warnings)

    extra_missing = [column for column in FILL_COLUMNS if column not in frame.columns]
    if extra_missing:
        warnings.append(f"Optional columns missing: {', '.join(extra_missing)}")

    sides = frame["side"].astype(str).str.upper().str.strip()
    invalid_sides = frame.loc[~sides.isin(VALID_FILL_SIDES)]
    if not invalid_sides.empty:
        errors.append(f"Invalid side values at rows: {_row_numbers(invalid_sides.index)}")

    quantity = pd.to_numeric(frame["quantity"], errors="coerce")
    invalid_quantity = frame.loc[quantity.isna() | (quantity <= 0)]
    if not invalid_quantity.empty:
        errors.append(f"Non-positive quantity at rows: {_row_numbers(invalid_quantity.index)}")

    fill_price = pd.to_numeric(frame["fill_price"], errors="coerce")
    invalid_price = frame.loc[fill_price.isna() | (fill_price <= 0)]
    if not invalid_price.empty:
        errors.append(f"Non-positive fill_price at rows: {_row_numbers(invalid_price.index)}")

    parsed_dates = pd.to_datetime(frame["fill_date"], errors="coerce")
    invalid_dates = frame.loc[parsed_dates.isna()]
    if not invalid_dates.empty:
        errors.append(f"Unparseable fill_date at rows: {_row_numbers(invalid_dates.index)}")

    return FillValidationResult(not errors, len(frame), errors, warnings)


def write_fills_template(path: str | Path, *, overwrite: bool = False) -> Path:
    """Write an empty manual paper fills CSV template."""

    output = Path(path)
    if output.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file without --overwrite: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=FILL_COLUMNS).to_csv(output, index=False)
    return output


def _handle_replay_run(args: argparse.Namespace) -> int:
    settings = _workflow_settings_from_args(args, "replay_run")
    try:
        result = run_replay(
            args.date,
            universe_name=args.universe,
            top_n=args.top,
            holding_horizon=args.horizon,
            config=settings,
            snapshot_manifest_path=args.snapshot_manifest,
        )
    except SnapshotQualityPreflightError as exc:
        return _print_snapshot_preflight_error(exc)

    print(f"run_id: {result.run_id}")
    print(f"decision_date: {result.decision_date.date()}")
    print(f"report_path: {result.report_path}")
    print(f"candidate_count: {result.performance_summary.get('number_of_candidates')}")
    print(f"simulated_buy_count: {result.performance_summary.get('number_of_simulated_buys')}")
    _print_snapshot_preflight_summary(result.audit_metadata)
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_batch_replay(args: argparse.Namespace) -> int:
    settings = _workflow_settings_from_args(args, "batch_replay")
    try:
        result = run_batch_replay(
            _parse_date_values(args.dates),
            universe_name=args.universe,
            top_n=args.top,
            holding_horizon=args.horizon,
            config=settings,
            snapshot_manifest_path=args.snapshot_manifest,
        )
    except SnapshotQualityPreflightError as exc:
        return _print_snapshot_preflight_error(exc)

    print(f"batch_id: {result.batch_id}")
    print(f"batch_report_path: {result.artifact_paths['batch_report']}")
    print(f"executed_date_count: {len(result.executed_decision_dates)}")
    print(f"skipped_date_count: {len(result.skipped_decision_dates)}")
    _print_snapshot_preflight_summary(result.snapshot_quality_preflight or {})
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_parameter_calibration(args: argparse.Namespace) -> int:
    settings = _workflow_settings_from_args(args, "calibration")
    try:
        result = run_parameter_calibration(
            _parse_date_values(args.dates),
            universe_name=args.universe,
            config=settings,
            snapshot_manifest_path=args.snapshot_manifest,
        )
    except SnapshotQualityPreflightError as exc:
        return _print_snapshot_preflight_error(exc)

    print(f"calibration_id: {result.calibration_id}")
    print(f"calibration_report_path: {result.artifact_paths['calibration_report']}")
    print(f"parameter_set_count: {len(result.parameter_sets)}")
    print(
        "best_parameter_set: "
        f"{result.best_parameter_set.parameter_set_id if result.best_parameter_set is not None else ''}"
    )
    _print_snapshot_preflight_summary(result.snapshot_quality_preflight or {})
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_walk_forward(args: argparse.Namespace) -> int:
    settings = _workflow_settings_from_args(args, "walk_forward")
    try:
        result = run_walk_forward_validation(
            train_dates=_parse_date_values(args.train_dates),
            validation_dates=_parse_date_values(args.validation_dates),
            test_dates=_parse_date_values(args.test_dates),
            universe_name=args.universe,
            config=settings,
            snapshot_manifest_path=args.snapshot_manifest,
        )
    except SnapshotQualityPreflightError as exc:
        return _print_snapshot_preflight_error(exc)

    print(f"walk_forward_id: {result.walk_forward_id}")
    print(f"walk_forward_report_path: {result.artifact_paths['walk_forward_report']}")
    print(
        "selected_parameter_set: "
        f"{result.selected_parameter_set.parameter_set_id if result.selected_parameter_set is not None else ''}"
    )
    _print_snapshot_preflight_summary(result.snapshot_quality_preflight or {})
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_current_candidates(args: argparse.Namespace) -> int:
    settings = _workflow_settings_from_args(args, "current_candidates")
    preflight_override = None
    if args.enable_snapshot_preflight:
        preflight_override = True
    if args.disable_snapshot_preflight:
        preflight_override = False
    try:
        result = generate_current_candidates(
            args.date,
            universe_name=args.universe,
            top_n=args.top,
            config=settings,
            snapshot_manifest_path=args.snapshot_manifest,
            enable_snapshot_preflight=preflight_override,
            selection_profile=args.selection_profile,
        )
    except SnapshotQualityPreflightError as exc:
        return _print_snapshot_preflight_error(exc)

    print(f"current_candidate_run_id: {result.run_id}")
    print(f"decision_date: {result.decision_date.date()}")
    print(f"selection_profile: {result.audit_metadata.get('selection_profile', 'default')}")
    print(f"demo_mode: {result.audit_metadata.get('demo_mode', False)}")
    print(f"candidate_count: {result.candidate_count}")
    print(f"candidates_path: {result.artifact_paths['candidates']}")
    print(f"report_path: {result.artifact_paths['current_candidates_report']}")
    _print_snapshot_preflight_summary(result.audit_metadata)
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_current_candidates_index(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"include_missing_metadata": bool(args.include_missing_metadata)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "current_candidate_artifact_index": settings.current_candidate_artifact_index.model_copy(update=updates)
        }
    )
    result = build_current_candidate_artifact_index(settings=settings)
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index report path: {result.artifact_paths['current_candidate_artifact_index']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_current_candidates_health(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.index:
        updates["index_path"] = Path(args.index)
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "current_candidate_artifact_health": settings.current_candidate_artifact_health.model_copy(update=updates)
        }
    )
    result = check_current_candidate_artifact_health(
        index_path=args.index,
        root=None if args.index else args.root,
        settings=settings,
    )
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Report path: {result.artifact_paths['current_candidate_artifact_health_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict and not args.allow_warn:
        return 1
    return 0


def _handle_current_to_paper(args: argparse.Namespace) -> int:
    if not args.candidates and not args.index and not args.root:
        raise ValueError("Provide --candidates, --index, or --root")
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    handoff_updates = {}
    if args.output_dir:
        output_dir = Path(args.output_dir)
        handoff_updates["output_dir"] = output_dir
        settings = settings.model_copy(
            update={
                "daily_paper_runner": settings.daily_paper_runner.model_copy(
                    update={"output_dir": output_dir / "paper_daily"}
                ),
                "paper_reconciliation": settings.paper_reconciliation.model_copy(
                    update={"output_dir": output_dir / "reconciliation"}
                ),
                "current_candidate_artifact_health": settings.current_candidate_artifact_health.model_copy(
                    update={"output_dir": output_dir / "current_candidate_health"}
                ),
            }
        )
    if args.allow_health_warn:
        handoff_updates["allow_health_warn"] = True
    if handoff_updates:
        settings = settings.model_copy(
            update={
                "current_to_paper_handoff": settings.current_to_paper_handoff.model_copy(
                    update=handoff_updates
                )
            }
        )
    result = run_current_to_paper_handoff(
        paper_date=args.paper_date,
        current_candidate_index_path=args.index,
        current_candidate_root=args.root,
        candidates_path=args.candidates,
        decision_date=args.decision_date,
        universe_name=args.universe,
        run_id=args.run_id,
        fills_path=args.fills,
        journal_id=args.journal_id,
        allow_health_warn=args.allow_health_warn,
        skip_health_check=args.skip_health_check,
        config=settings,
    )
    print(f"handoff_id: {result.handoff_id}")
    print(f"selected_candidates_path: {result.selected_candidates_path}")
    if result.health_status:
        print(f"health_status: {result.health_status}")
    print(f"paper_journal_id: {result.paper_journal_id}")
    print(f"paper_report_path: {result.paper_artifact_paths['paper_report']}")
    print(f"handoff_report_path: {result.handoff_artifact_paths['handoff_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_current_to_paper_review(args: argparse.Namespace) -> int:
    if not args.decisions and not args.handoff_dir:
        raise ValueError("Provide --decisions or --handoff-dir")
    if args.decisions and args.handoff_dir:
        raise ValueError("Provide either --decisions or --handoff-dir, not both")
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    if args.output_dir:
        settings = settings.model_copy(
            update={
                "current_to_paper_review_handoff": settings.current_to_paper_review_handoff.model_copy(
                    update={"output_dir": Path(args.output_dir)}
                )
            }
        )
    result = run_current_to_paper_review_handoff(
        decisions_path=args.decisions,
        handoff_artifact_dir=args.handoff_dir,
        reviewer_id=args.reviewer_id,
        config=settings,
    )
    print(f"review_handoff_id: {result.review_handoff_id}")
    print(f"decision_count: {result.decision_count}")
    print(f"template_path: {result.template_path}")
    print(f"report_path: {result.report_path}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_paper_daily(args: argparse.Namespace) -> int:
    if not args.candidates and not args.reviewed_decisions:
        raise ValueError("Either --candidates or --reviewed-decisions is required")
    result = run_daily_paper_trading(
        args.date,
        candidates_path=args.candidates,
        reviewed_decisions_path=args.reviewed_decisions,
        fills_path=args.fills,
        mark_prices=args.mark_prices,
        output_dir=args.output_dir,
        journal_id=args.journal_id,
        config=args.config,
    )
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Report path: {result.artifact_paths['paper_report']}")
    print(f"decision_count: {result.decision_count}")
    print(f"fill_count: {result.fill_count}")
    print(f"open_position_count: {result.open_position_count}")
    print(f"closed_trade_count: {result.closed_trade_count}")
    print(f"reviewed_decisions_used: {result.reviewed_decisions_used}")
    if result.reviewed_decisions_path is not None:
        print(f"reviewed_decisions_path: {result.reviewed_decisions_path}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_validate_fills(args: argparse.Namespace) -> int:
    result = validate_fills_csv(args.fills)
    print(f"fills_path: {args.fills}")
    print(f"row_count: {result.row_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    if result.valid:
        print("Validation passed.")
        print("No live trading or broker API was invoked.")
        return 0
    print("Validation failed.", file=sys.stderr)
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


def _handle_template_fills(args: argparse.Namespace) -> int:
    output = write_fills_template(args.output, overwrite=bool(args.overwrite))
    print(f"Wrote fills template: {output}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_reconcile_fills(args: argparse.Namespace) -> int:
    decisions_path = Path(args.decisions)
    fills_path = Path(args.fills)
    if not decisions_path.exists():
        raise FileNotFoundError(f"Decisions CSV not found: {decisions_path}")
    if not fills_path.exists():
        raise FileNotFoundError(f"Fills CSV not found: {fills_path}")
    settings = load_settings(args.config) if args.config else None
    if args.output_dir:
        project_settings = settings or load_settings(Path("config/default.yaml"))
        settings = project_settings.model_copy(
            update={
                "paper_reconciliation": project_settings.paper_reconciliation.model_copy(
                    update={"output_dir": Path(args.output_dir)}
                )
            }
        )
    result = reconcile_paper_fills(pd.read_csv(decisions_path), pd.read_csv(fills_path), settings=settings)
    print(f"Reconciliation status: {result.status}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Report path: {result.artifact_paths['reconciliation_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL" and not args.allow_fail:
        return 1
    return 0


def _handle_review_decisions(args: argparse.Namespace) -> int:
    decisions_path = Path(args.decisions)
    updates_path = Path(args.updates)
    if not decisions_path.exists():
        raise FileNotFoundError(f"Decisions CSV not found: {decisions_path}")
    if not updates_path.exists():
        raise FileNotFoundError(f"Review updates CSV not found: {updates_path}")
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    review_updates = {}
    if args.output_dir:
        review_updates["output_dir"] = Path(args.output_dir)
    if args.allow_pending:
        review_updates["allow_pending_reviews"] = True
    if args.health_check:
        review_updates["enable_template_health_check"] = True
    if args.require_template_health_pass:
        review_updates["enable_template_health_check"] = True
        review_updates["require_template_health_pass"] = True
    if args.allow_template_health_warn:
        review_updates["allow_template_health_warn"] = True
    if review_updates:
        settings = settings.model_copy(
            update={
                "paper_review": settings.paper_review.model_copy(update=review_updates)
            }
        )
    if args.template_health_output_dir:
        settings = settings.model_copy(
            update={
                "paper_review_template_health": settings.paper_review_template_health.model_copy(
                    update={"output_dir": Path(args.template_health_output_dir)}
                )
            }
        )
    decisions_frame = pd.read_csv(decisions_path)
    updates_frame = pd.read_csv(updates_path)
    template_health_metadata = None
    if settings.paper_review.enable_template_health_check:
        health_result = check_review_template_health(
            updates_frame,
            decisions=decisions_frame,
            settings=settings,
        )
        template_health_metadata = _template_health_metadata(health_result)
        print(f"Template health status: {health_result.status}")
        print(f"Template health report path: {health_result.artifact_paths['review_template_health_report']}")
        print(f"Template health issue_count: {health_result.issue_count}")
        print(f"Template health error_count: {health_result.error_count}")
        print(f"Template health warning_count: {health_result.warning_count}")
        if health_result.status == "FAIL":
            print("No live trading or broker API was invoked.")
            return 1
        if health_result.status == "WARN" and settings.paper_review.require_template_health_pass:
            print("No live trading or broker API was invoked.")
            return 1
        if health_result.status == "WARN" and not settings.paper_review.allow_template_health_warn:
            print("No live trading or broker API was invoked.")
            return 1
    result = apply_paper_review_updates(
        decisions_frame,
        updates_frame,
        reviewer_id=args.reviewer_id,
        settings=settings,
        template_health_metadata=template_health_metadata,
    )
    summary = result.review_summary.iloc[0].to_dict() if not result.review_summary.empty else {}
    print(f"review_id: {result.review_id}")
    print(f"total_decisions: {summary.get('total_decisions', 0)}")
    print(f"approved_count: {summary.get('approved_count', 0)}")
    print(f"rejected_count: {summary.get('rejected_count', 0)}")
    print(f"watch_only_count: {summary.get('watch_only_count', 0)}")
    print(f"pending_count: {summary.get('pending_count', 0)}")
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Report path: {result.artifact_paths['paper_review_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_review_template_health(args: argparse.Namespace) -> int:
    updates_path = Path(args.updates)
    if not updates_path.exists():
        raise FileNotFoundError(f"Review updates CSV not found: {updates_path}")
    decisions_path = Path(args.decisions) if args.decisions else None
    if decisions_path is not None and not decisions_path.exists():
        raise FileNotFoundError(f"Decisions CSV not found: {decisions_path}")
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    health_updates = {}
    if args.output_dir:
        health_updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "paper_review_template_health": settings.paper_review_template_health.model_copy(update=health_updates)
        }
    )
    result = check_review_template_health(
        pd.read_csv(updates_path),
        decisions=pd.read_csv(decisions_path) if decisions_path is not None else None,
        settings=settings,
    )
    print(f"Review template health status: {result.status}")
    print(f"update_row_count: {result.update_row_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Report path: {result.artifact_paths['review_template_health_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict and not args.allow_warn:
        return 1
    return 0


def _handle_paper_index(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {
        "artifact_type": args.artifact_type,
        "include_missing_metadata": bool(args.include_missing_metadata),
    }
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "paper_artifact_index": settings.paper_artifact_index.model_copy(update=updates)
        }
    )
    result = build_paper_artifact_index(settings=settings)
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index report path: {result.artifact_paths['paper_artifact_index']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_paper_health_check(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.index:
        updates["index_path"] = Path(args.index)
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "paper_artifact_health": settings.paper_artifact_health.model_copy(update=updates)
        }
    )
    result = check_paper_artifact_health(
        index_path=args.index,
        root=None if args.index else args.root,
        settings=settings,
    )
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Report path: {result.artifact_paths['artifact_health_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict and not args.allow_warn:
        return 1
    return 0


def _handle_paper_workflow_status(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.current_candidates_root:
        updates["current_candidates_root"] = Path(args.current_candidates_root)
    if args.paper_trading_root:
        updates["paper_trading_root"] = Path(args.paper_trading_root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "paper_workflow_status": settings.paper_workflow_status.model_copy(update=updates)
        }
    )
    result = run_paper_workflow_status(
        root=args.root,
        current_candidates_root=args.current_candidates_root,
        paper_trading_root=args.paper_trading_root,
        decision_date=args.decision_date,
        universe_name=args.universe,
        output_dir=args.output_dir,
        config=settings,
    )
    print(f"Workflow status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_decision_date: {result.latest_decision_date}")
    print(f"next_manual_action: {result.next_manual_action}")
    print(f"Report path: {result.artifact_paths['paper_workflow_status_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict:
        return 1
    return 0


def _handle_research_status(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.data_preparation_root:
        updates["data_preparation_root"] = Path(args.data_preparation_root)
    if args.current_candidates_root:
        updates["current_candidates_root"] = Path(args.current_candidates_root)
    if args.paper_trading_root:
        updates["paper_trading_root"] = Path(args.paper_trading_root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "local_research_dashboard": settings.local_research_dashboard.model_copy(update=updates)
        }
    )
    result = run_local_research_dashboard(
        root=args.root,
        data_preparation_root=args.data_preparation_root,
        current_candidates_root=args.current_candidates_root,
        paper_trading_root=args.paper_trading_root,
        decision_date=args.decision_date,
        universe_name=args.universe,
        output_dir=args.output_dir,
        config=settings,
    )
    print(f"Research status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_decision_date: {result.latest_decision_date}")
    print(f"next_manual_action: {result.next_manual_action}")
    print(f"Report path: {result.artifact_paths['local_research_dashboard']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict:
        return 1
    return 0


def _handle_data_source_fetch(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    if args.allow_real_data:
        settings = settings.model_copy(
            update={
                "data_sources": settings.data_sources.model_copy(
                    update={
                        "allow_network_sources": True,
                        "allow_real_data_fetch": True,
                    }
                )
            }
        )
    request = DataSourceRequest(
        source=args.source,
        dataset_type=args.dataset_type,
        input_path=args.input,
        output_dir=args.output_dir,
        revision_id=args.revision_id,
        allow_real_data=bool(args.allow_real_data),
        symbol=args.symbol,
        start_date=args.start_date,
        end_date=args.end_date,
        as_of_date=args.as_of_date,
        market_type=args.market_type,
    )
    result = run_data_source_fetch(request, settings=settings)
    print(f"source: {result.source}")
    print(f"dataset_type: {result.dataset_type}")
    print(f"run_id: {result.run_id}")
    print(f"row_count: {result.row_count}")
    print(f"raw_data: {result.artifact_paths['raw_data']}")
    print(f"metadata: {result.artifact_paths['metadata']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_data_source_health(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    if args.output_dir:
        settings = settings.model_copy(
            update={
                "data_source_health": settings.data_source_health.model_copy(
                    update={"output_dir": Path(args.output_dir)}
                )
            }
        )
    result = run_data_source_health_check(
        source=args.source,
        dataset_type=args.dataset_type,
        input_path=args.input,
        allow_real_data=bool(args.allow_real_data),
        symbol=args.symbol,
        start_date=args.start_date,
        end_date=args.end_date,
        requested_upstream=args.requested_upstream,
        as_of_date=args.as_of_date,
        market_type=args.market_type,
        output_dir=args.output_dir,
        config=settings,
    )
    first_pass = result.health_frame[result.health_frame["status"] == "PASS"]
    selected = first_pass.iloc[0].to_dict() if not first_pass.empty else {}
    print(f"Data source health status: {result.status}")
    print(f"health_check_id: {result.health_check_id}")
    print(f"check_count: {len(result.health_frame)}")
    print(f"issue_count: {result.issue_count}")
    print(f"warning_count: {result.warning_count}")
    print(f"error_count: {result.error_count}")
    print(f"row_count: {selected.get('row_count', 0)}")
    print(f"successful_upstream: {selected.get('successful_upstream', '')}")
    print(f"successful_function: {selected.get('successful_function', '')}")
    print(f"Report path: {result.artifact_paths['data_source_health_report']}")
    print(f"Results CSV path: {result.artifact_paths['data_source_health_results']}")
    print(f"Summary CSV path: {result.artifact_paths['data_source_health_summary']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_market_cache_ingest(args: argparse.Namespace) -> int:
    settings = _market_cache_settings_from_args(args)
    result = ingest_market_cache_csv(
        args.input,
        metadata_path=args.metadata,
        cache_path=args.cache_path,
        output_dir=args.output_dir,
        config=settings,
    )
    print(f"Market cache status: {result.status}")
    print(f"cache_run_id: {result.cache_run_id}")
    print(f"cache_path: {result.cache_path}")
    print(f"ingested_row_count: {result.row_count}")
    print(f"cache_row_count: {result.cache_row_count}")
    print(f"symbol_count: {result.symbol_count}")
    print(f"Report path: {result.artifact_paths['market_cache_report']}")
    print(f"Summary CSV path: {result.artifact_paths['market_cache_summary']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0 if result.status != "FAIL" else 1


def _handle_market_cache_query(args: argparse.Namespace) -> int:
    settings = _market_cache_settings_from_args(args)
    result = query_market_cache(
        symbol=args.symbol,
        start_date=args.start_date,
        end_date=args.end_date,
        cache_path=args.cache_path,
        output_path=args.output,
        config=settings,
    )
    print(f"Market cache query status: {result.status}")
    print(f"cache_path: {result.cache_path}")
    print(f"symbol: {result.symbol}")
    print(f"row_count: {result.row_count}")
    if not result.result_frame.empty:
        print(f"date_range: {result.result_frame['trade_date'].min()} to {result.result_frame['trade_date'].max()}")
    else:
        print("date_range: ")
    if result.output_path is not None:
        print(f"output_path: {result.output_path}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0 if result.status != "FAIL" else 1


def _handle_market_cache_status(args: argparse.Namespace) -> int:
    settings = _market_cache_settings_from_args(args)
    result = summarize_market_cache_status(
        cache_path=args.cache_path,
        output_dir=args.output_dir,
        config=settings,
    )
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Market cache status: {result.status}")
    print(f"cache_run_id: {result.cache_run_id}")
    print(f"cache_path: {result.cache_path}")
    print(f"row_count: {summary.get('cache_row_count', 0)}")
    print(f"symbol_count: {summary.get('symbol_count', 0)}")
    print(f"date_range: {summary.get('min_trade_date', '')} to {summary.get('max_trade_date', '')}")
    print(f"source_counts: {summary.get('source_counts', '{}')}")
    print(f"upstream_counts: {summary.get('upstream_counts', '{}')}")
    print(f"Report path: {result.artifact_paths['market_cache_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0 if result.status != "FAIL" else 1


def _handle_universe_overlay(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"allow_override_existing": bool(args.allow_override_existing)}
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "universe_overlay": settings.universe_overlay.model_copy(update=updates)
        }
    )
    result = run_universe_overlay(
        args.base_universe,
        args.overlay,
        output_dir=args.output_dir,
        allow_override_existing=bool(args.allow_override_existing),
        settings=settings,
    )
    print(f"overlay_run_id: {result.overlay_run_id}")
    print(f"merged_universe_path: {result.artifact_paths['raw_data']}")
    print(f"added_symbol_count: {result.added_symbol_count}")
    print(f"overridden_symbol_count: {result.overridden_symbol_count}")
    print(f"report_path: {result.artifact_paths['universe_overlay_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_data_pipeline(args: argparse.Namespace) -> int:
    if args.manifest and args.dataset_type:
        raise ValueError("Use either --manifest or --dataset-type, not both")
    if not args.manifest and not args.dataset_type:
        raise ValueError("data-pipeline requires --dataset-type for single mode or --manifest for multi-dataset mode")
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    pipeline_updates = {"allow_real_data": bool(args.allow_real_data)}
    if args.output_dir:
        pipeline_updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "data_pipeline": settings.data_pipeline.model_copy(update=pipeline_updates)
        }
    )
    if args.manifest:
        datasets = load_data_pipeline_manifest(args.manifest)
    else:
        datasets = [
            {
                "dataset_type": args.dataset_type,
                "source": args.source or settings.data_sources.default_source,
                "input_path": args.input,
                "allow_real_data": bool(args.allow_real_data),
                "symbol": args.symbol,
                "start_date": args.start_date,
                "end_date": args.end_date,
                "as_of_date": args.as_of_date,
                "market_type": args.market_type,
            }
        ]
    result = run_data_source_ingestion_pipeline(
        datasets,
        config=settings,
        output_dir=args.output_dir,
        run_data_quality=not args.skip_data_quality,
        build_snapshot_manifest=not args.skip_snapshot_manifest,
    )
    print(f"Data pipeline status: {result.status}")
    print(f"pipeline_id: {result.pipeline_id}")
    for dataset_type, path in sorted(result.processed_paths.items()):
        print(f"processed_{dataset_type}: {path}")
    print(f"Report path: {result.artifact_paths['data_pipeline_report']}")
    if result.snapshot_manifest_path is not None:
        print(f"Snapshot manifest path: {result.snapshot_manifest_path}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_data_prep_index(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {
        "artifact_type": args.artifact_type,
        "include_missing_metadata": bool(args.include_missing_metadata),
    }
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "data_preparation_artifact_index": settings.data_preparation_artifact_index.model_copy(update=updates)
        }
    )
    result = build_data_preparation_artifact_index(settings=settings)
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index report path: {result.artifact_paths['data_preparation_artifact_index']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_data_prep_health(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.index:
        updates["index_path"] = Path(args.index)
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "data_preparation_artifact_health": settings.data_preparation_artifact_health.model_copy(update=updates)
        }
    )
    result = check_data_preparation_artifact_health(
        index_path=args.index,
        root=None if args.index else args.root,
        settings=settings,
    )
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Report path: {result.artifact_paths['data_preparation_artifact_health_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict and not args.allow_warn:
        return 1
    return 0


def _handle_data_prep_status(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.data_pipeline_root:
        updates["data_pipeline_root"] = Path(args.data_pipeline_root)
    if args.data_quality_root:
        updates["data_quality_root"] = Path(args.data_quality_root)
    if args.snapshot_quality_root:
        updates["snapshot_quality_root"] = Path(args.snapshot_quality_root)
    if args.current_candidates_root:
        updates["current_candidates_root"] = Path(args.current_candidates_root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "data_preparation_workflow_status": settings.data_preparation_workflow_status.model_copy(update=updates)
        }
    )
    result = run_data_preparation_workflow_status(
        root=args.root,
        data_pipeline_root=args.data_pipeline_root,
        data_quality_root=args.data_quality_root,
        snapshot_quality_root=args.snapshot_quality_root,
        current_candidates_root=args.current_candidates_root,
        decision_date=args.decision_date,
        universe_name=args.universe,
        output_dir=args.output_dir,
        config=settings,
    )
    print(f"Workflow status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_pipeline_id: {result.latest_pipeline_id}")
    print(f"latest_snapshot_id: {result.latest_snapshot_id}")
    print(f"latest_decision_date: {result.latest_decision_date}")
    print(f"next_manual_action: {result.next_manual_action}")
    print(f"Report path: {result.artifact_paths['data_preparation_workflow_status_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict:
        return 1
    return 0


def _handle_ingest_market(args: argparse.Namespace) -> int:
    return _print_ingestion_result(
        ingest_market_data_csv(args.input, output_dir=args.output_dir, settings=_optional_settings(args.config))
    )


def _handle_ingest_universe(args: argparse.Namespace) -> int:
    return _print_ingestion_result(
        ingest_universe_snapshot_csv(args.input, output_dir=args.output_dir, settings=_optional_settings(args.config))
    )


def _handle_ingest_benchmark(args: argparse.Namespace) -> int:
    return _print_ingestion_result(
        ingest_benchmark_data_csv(args.input, output_dir=args.output_dir, settings=_optional_settings(args.config))
    )


def _handle_ingest_corporate_actions(args: argparse.Namespace) -> int:
    return _print_ingestion_result(
        ingest_corporate_actions_csv(args.input, output_dir=args.output_dir, settings=_optional_settings(args.config))
    )


def _handle_ingest_calendar(args: argparse.Namespace) -> int:
    return _print_ingestion_result(
        ingest_trading_calendar_csv(args.input, output_dir=args.output_dir, settings=_optional_settings(args.config))
    )


def _handle_data_quality(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    if args.strict:
        settings = settings.model_copy(
            update={
                "data_quality": settings.data_quality.model_copy(update={"strict": True})
            }
        )
    result = run_data_quality_checks(
        args.input,
        args.dataset_type,
        output_dir=args.output_dir,
        settings=settings,
    )
    print(f"Data quality status: {result.status}")
    print(f"dataset_type: {result.dataset_type}")
    print(f"row_count: {result.row_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"warning_count: {result.warning_count}")
    print(f"error_count: {result.error_count}")
    print(f"Report path: {result.artifact_paths['data_quality_report']}")
    print("No live trading or broker API was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_snapshot_quality(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    if args.strict:
        settings = settings.model_copy(
            update={
                "snapshot_quality_gate": settings.snapshot_quality_gate.model_copy(
                    update={"fail_on_required_dataset_warn": True}
                )
            }
        )
    result = run_snapshot_quality_gate(
        args.manifest,
        output_dir=args.output_dir,
        settings=settings,
    )
    print(f"Snapshot quality status: {result.status}")
    print(f"snapshot_id: {result.snapshot_id}")
    print(f"failed_required_datasets: {', '.join(result.failed_required_datasets)}")
    print(f"failed_optional_datasets: {', '.join(result.failed_optional_datasets)}")
    print(f"warning_count: {result.warning_count}")
    print(f"error_count: {result.error_count}")
    print(f"Report path: {result.artifact_paths['snapshot_quality_gate_report']}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict and not args.allow_warn:
        return 1
    return 0


def _add_snapshot_preflight_arguments(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("snapshot quality preflight")
    group.add_argument("--snapshot-manifest", help="Snapshot manifest JSON path")

    enable_group = group.add_mutually_exclusive_group()
    enable_group.add_argument(
        "--enable-snapshot-preflight",
        action="store_true",
        help="Enable snapshot quality preflight for this workflow",
    )
    enable_group.add_argument(
        "--disable-snapshot-preflight",
        action="store_true",
        help="Force snapshot quality preflight off for this workflow",
    )

    fail_group = group.add_mutually_exclusive_group()
    fail_group.add_argument(
        "--block-on-fail",
        dest="snapshot_block_on_fail",
        action="store_true",
        default=None,
        help="Exit non-zero when snapshot preflight status is FAIL",
    )
    fail_group.add_argument(
        "--allow-fail",
        dest="snapshot_block_on_fail",
        action="store_false",
        help="Allow workflow to continue when snapshot preflight status is FAIL",
    )

    warn_group = group.add_mutually_exclusive_group()
    warn_group.add_argument(
        "--block-on-warn",
        dest="snapshot_block_on_warn",
        action="store_true",
        default=None,
        help="Exit non-zero when snapshot preflight status is WARN",
    )
    warn_group.add_argument(
        "--allow-warn",
        dest="snapshot_block_on_warn",
        action="store_false",
        help="Allow workflow to continue when snapshot preflight status is WARN",
    )


def _workflow_settings_from_args(args: argparse.Namespace, section_name: str):
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    if args.output_dir:
        current_section = getattr(settings, section_name)
        settings = settings.model_copy(
            update={section_name: current_section.model_copy(update={"output_dir": Path(args.output_dir)})}
        )
    return _apply_snapshot_preflight_args(settings, args)


def _market_cache_settings_from_args(args: argparse.Namespace):
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {}
    if getattr(args, "cache_path", None):
        updates["cache_path"] = Path(args.cache_path)
    if getattr(args, "output_dir", None):
        updates["output_dir"] = Path(args.output_dir)
    if not updates:
        return settings
    return settings.model_copy(
        update={
            "market_data_cache": settings.market_data_cache.model_copy(update=updates)
        }
    )


def _apply_snapshot_preflight_args(settings, args: argparse.Namespace):
    updates = {}
    if args.snapshot_manifest:
        updates["manifest_path"] = Path(args.snapshot_manifest)
        updates["enabled"] = True
    if args.enable_snapshot_preflight:
        updates["enabled"] = True
    if args.disable_snapshot_preflight:
        updates["enabled"] = False
    if args.snapshot_block_on_fail is not None:
        updates["block_on_fail"] = bool(args.snapshot_block_on_fail)
    if args.snapshot_block_on_warn is not None:
        updates["block_on_warn"] = bool(args.snapshot_block_on_warn)
    if not updates:
        return settings
    return settings.model_copy(
        update={
            "snapshot_quality_preflight": settings.snapshot_quality_preflight.model_copy(update=updates)
        }
    )


def _parse_date_values(values: Sequence[str] | None) -> list[str]:
    if not values:
        return []
    dates: list[str] = []
    for value in values:
        parts = [part.strip() for part in str(value).split(",")]
        dates.extend(part for part in parts if part)
    return dates


def _print_snapshot_preflight_summary(metadata: dict) -> None:
    if not metadata.get("snapshot_quality_preflight_enabled"):
        return
    print(f"Snapshot quality status: {metadata.get('snapshot_quality_status')}")
    report_path = metadata.get("snapshot_quality_report_path")
    if report_path:
        print(f"Snapshot quality report path: {report_path}")
    gate_id = metadata.get("snapshot_quality_gate_id")
    if gate_id:
        print(f"Snapshot quality gate id: {gate_id}")
    for warning in metadata.get("snapshot_quality_warnings") or []:
        print(f"WARNING: {warning}")


def _print_snapshot_preflight_error(exc: SnapshotQualityPreflightError) -> int:
    if exc.preflight_result is not None:
        _print_snapshot_preflight_summary(exc.preflight_result.metadata_fields())
    print(f"ERROR: {exc}", file=sys.stderr)
    print("No live trading or broker API was invoked.")
    return 1


def _template_health_metadata(result) -> dict:
    return {
        "template_health_status": result.status,
        "template_health_report_path": str(result.artifact_paths["review_template_health_report"]),
        "template_health_issue_count": result.issue_count,
        "template_health_error_count": result.error_count,
        "template_health_warning_count": result.warning_count,
        "template_health_check_id": result.health_check_id,
    }


def _optional_settings(config_path: str | None):
    return load_settings(config_path) if config_path else None


def _print_ingestion_result(result) -> int:
    print(f"dataset_type: {result.dataset_type}")
    print(f"row_count: {result.row_count}")
    print(f"cleaned_csv: {result.artifact_paths['cleaned_csv']}")
    print(f"validation_report: {result.artifact_paths['validation_report']}")
    print(f"metadata: {result.artifact_paths['metadata']}")
    print(f"warning_count: {result.validation.warning_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _row_numbers(index: pd.Index) -> str:
    return ", ".join(str(int(value) + 2) for value in index)


if __name__ == "__main__":
    raise SystemExit(main())
