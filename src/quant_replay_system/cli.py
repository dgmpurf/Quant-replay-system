"""Command line helpers for local-only paper trading workflows."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd

from quant_replay_system.batch_replay import run_batch_replay
from quant_replay_system.calibration import run_parameter_calibration
from quant_replay_system.calibration_to_signal_semantics import run_calibration_to_signal_semantics
from quant_replay_system.calibration_to_signal_semantics_health import check_calibration_to_signal_semantics_health
from quant_replay_system.calibration_to_signal_semantics_index import build_calibration_to_signal_semantics_index
from quant_replay_system.calibration_to_signal_semantics_status import run_calibration_to_signal_semantics_status
from quant_replay_system.advisory_profile_calibration import run_advisory_profile_calibration
from quant_replay_system.advisory_profile_calibration_health import check_advisory_profile_calibration_health
from quant_replay_system.advisory_profile_calibration_index import build_advisory_profile_calibration_index
from quant_replay_system.advisory_profile_calibration_status import run_advisory_profile_calibration_status
from quant_replay_system.advisory_conversation import run_advisory_conversation
from quant_replay_system.advisory_conversation_health import check_advisory_conversation_health
from quant_replay_system.advisory_conversation_index import build_advisory_conversation_index
from quant_replay_system.advisory_conversation_status import run_advisory_conversation_status
from quant_replay_system.config import load_settings
from quant_replay_system.current_candidate_artifact_health import check_current_candidate_artifact_health
from quant_replay_system.current_candidate_artifact_index import build_current_candidate_artifact_index
from quant_replay_system.current_candidates_backfill_plan import build_current_candidates_backfill_plan
from quant_replay_system.current_candidates_backfill_execution_manifest import (
    build_current_candidates_backfill_execution_manifest,
)
from quant_replay_system.current_candidates_backfill_execution_manifest_health import (
    check_current_candidates_backfill_execution_manifest_health,
)
from quant_replay_system.current_candidates_backfill_execution_manifest_index import (
    build_current_candidates_backfill_execution_manifest_index,
)
from quant_replay_system.current_candidates_backfill_execution_manifest_status import (
    run_current_candidates_backfill_execution_manifest_status,
)
from quant_replay_system.current_candidates_backfill_plan_health import check_current_candidates_backfill_plan_health
from quant_replay_system.current_candidates_backfill_plan_index import build_current_candidates_backfill_plan_index
from quant_replay_system.current_candidates_backfill_plan_status import run_current_candidates_backfill_plan_status
from quant_replay_system.current_candidates import generate_current_candidates
from quant_replay_system.current_to_paper_handoff import run_current_to_paper_handoff
from quant_replay_system.current_to_paper_review_handoff import run_current_to_paper_review_handoff
from quant_replay_system.point_in_time_universe_overlay_plan import build_point_in_time_universe_overlay_plan
from quant_replay_system.point_in_time_universe_overlay_plan_health import (
    check_point_in_time_universe_overlay_plan_health,
)
from quant_replay_system.point_in_time_universe_overlay_plan_index import (
    build_point_in_time_universe_overlay_plan_index,
)
from quant_replay_system.point_in_time_universe_overlay_plan_status import (
    run_point_in_time_universe_overlay_plan_status,
)
from quant_replay_system.point_in_time_universe_overlay_review import build_pit_universe_overlay_review
from quant_replay_system.point_in_time_universe_overlay_export_readiness import (
    build_pit_universe_overlay_export_readiness,
)
from quant_replay_system.point_in_time_universe_overlay_export_readiness_health import (
    check_pit_universe_overlay_export_readiness_health,
)
from quant_replay_system.point_in_time_universe_overlay_export_readiness_index import (
    build_pit_universe_overlay_export_readiness_index,
)
from quant_replay_system.point_in_time_universe_overlay_export_readiness_status import (
    run_pit_universe_overlay_export_readiness_status,
)
from quant_replay_system.point_in_time_universe_export_staging import (
    build_pit_universe_export_staging,
)
from quant_replay_system.point_in_time_universe_export_staging_health import (
    check_pit_universe_export_staging_health,
)
from quant_replay_system.point_in_time_universe_export_staging_index import (
    build_pit_universe_export_staging_index,
)
from quant_replay_system.point_in_time_universe_export_staging_status import (
    run_pit_universe_export_staging_status,
)
from quant_replay_system.point_in_time_universe_evidence_completion_helper import (
    build_pit_universe_evidence_completion_helper,
)
from quant_replay_system.point_in_time_universe_evidence_completion_helper_health import (
    check_pit_universe_evidence_completion_helper_health,
)
from quant_replay_system.point_in_time_universe_evidence_completion_helper_index import (
    build_pit_universe_evidence_completion_helper_index,
)
from quant_replay_system.point_in_time_universe_evidence_completion_helper_status import (
    run_pit_universe_evidence_completion_helper_status,
)
from quant_replay_system.point_in_time_universe_evidence_review_worklist import (
    build_pit_universe_evidence_review_worklist,
)
from quant_replay_system.point_in_time_universe_evidence_review_worklist_health import (
    check_pit_universe_evidence_review_worklist_health,
)
from quant_replay_system.point_in_time_universe_evidence_review_worklist_index import (
    build_pit_universe_evidence_review_worklist_index,
)
from quant_replay_system.point_in_time_universe_evidence_review_worklist_status import (
    run_pit_universe_evidence_review_worklist_status,
)
from quant_replay_system.point_in_time_universe_evidence_update_ingestion import (
    build_pit_universe_evidence_update_ingestion,
)
from quant_replay_system.point_in_time_universe_evidence_update_ingestion_health import (
    check_pit_universe_evidence_update_ingestion_health,
)
from quant_replay_system.point_in_time_universe_evidence_update_ingestion_index import (
    build_pit_universe_evidence_update_ingestion_index,
)
from quant_replay_system.point_in_time_universe_evidence_update_ingestion_status import (
    run_pit_universe_evidence_update_ingestion_status,
)
from quant_replay_system.pit_evidence_checklist_validator import build_pit_evidence_checklist_validator
from quant_replay_system.pit_evidence_checklist_validator_health import check_pit_evidence_checklist_validator_health
from quant_replay_system.pit_evidence_checklist_validator_index import build_pit_evidence_checklist_validator_index
from quant_replay_system.pit_evidence_checklist_validator_status import run_pit_evidence_checklist_validator_status
from quant_replay_system.pit_evidence_policy_profile_comparison import (
    build_pit_evidence_policy_profile_comparison,
)
from quant_replay_system.pit_evidence_policy_profile_comparison_health import (
    check_pit_evidence_policy_profile_comparison_health,
)
from quant_replay_system.pit_evidence_policy_profile_comparison_index import (
    build_pit_evidence_policy_profile_comparison_index,
)
from quant_replay_system.pit_evidence_policy_profile_comparison_status import (
    run_pit_evidence_policy_profile_comparison_status,
)
from quant_replay_system.pit_official_status_evidence_packet import (
    build_pit_official_status_evidence_packet,
)
from quant_replay_system.pit_official_status_evidence_packet_health import (
    check_pit_official_status_evidence_packet_health,
)
from quant_replay_system.pit_official_status_evidence_packet_index import (
    build_pit_official_status_evidence_packet_index,
)
from quant_replay_system.pit_official_status_evidence_packet_status import (
    run_pit_official_status_evidence_packet_status,
)
from quant_replay_system.pit_official_status_evidence_packet_enrichment import (
    build_pit_official_status_evidence_packet_enrichment,
)
from quant_replay_system.pit_official_status_evidence_packet_enrichment_health import (
    check_pit_official_status_evidence_packet_enrichment_health,
)
from quant_replay_system.pit_official_status_evidence_packet_enrichment_index import (
    build_pit_official_status_evidence_packet_enrichment_index,
)
from quant_replay_system.pit_official_status_evidence_packet_enrichment_status import (
    run_pit_official_status_evidence_packet_enrichment_status,
)
from quant_replay_system.reviewer_no_hit_source_coverage_acceptance import (
    build_reviewer_no_hit_source_coverage_acceptance,
)
from quant_replay_system.reviewer_no_hit_source_coverage_acceptance_health import (
    check_reviewer_no_hit_source_coverage_acceptance_health,
)
from quant_replay_system.reviewer_no_hit_source_coverage_acceptance_index import (
    build_reviewer_no_hit_source_coverage_acceptance_index,
)
from quant_replay_system.reviewer_no_hit_source_coverage_acceptance_status import (
    run_reviewer_no_hit_source_coverage_acceptance_status,
)
from quant_replay_system.reviewer_no_hit_acceptance_downstream_impact import (
    build_reviewer_no_hit_acceptance_downstream_impact,
)
from quant_replay_system.reviewer_no_hit_acceptance_downstream_impact_health import (
    check_reviewer_no_hit_acceptance_downstream_impact_health,
)
from quant_replay_system.reviewer_no_hit_acceptance_downstream_impact_index import (
    build_reviewer_no_hit_acceptance_downstream_impact_index,
)
from quant_replay_system.reviewer_no_hit_acceptance_downstream_impact_status import (
    run_reviewer_no_hit_acceptance_downstream_impact_status,
)
from quant_replay_system.first_batch_reviewer_evidence_completion_plan import (
    build_first_batch_reviewer_evidence_completion_plan,
)
from quant_replay_system.first_batch_reviewer_evidence_completion_plan_health import (
    check_first_batch_reviewer_evidence_completion_plan_health,
)
from quant_replay_system.first_batch_reviewer_evidence_completion_plan_index import (
    build_first_batch_reviewer_evidence_completion_plan_index,
)
from quant_replay_system.first_batch_reviewer_evidence_completion_plan_status import (
    run_first_batch_reviewer_evidence_completion_plan_status,
)
from quant_replay_system.first_batch_partial_completion_impact import (
    build_first_batch_partial_completion_impact,
)
from quant_replay_system.first_batch_partial_completion_impact_health import (
    check_first_batch_partial_completion_impact_health,
)
from quant_replay_system.first_batch_partial_completion_impact_index import (
    build_first_batch_partial_completion_impact_index,
)
from quant_replay_system.first_batch_partial_completion_impact_status import (
    run_first_batch_partial_completion_impact_status,
)
from quant_replay_system.material_pit_evidence_gate_closure_plan import (
    build_material_pit_evidence_gate_closure_plan,
)
from quant_replay_system.material_pit_evidence_gate_closure_plan_health import (
    check_material_pit_evidence_gate_closure_plan_health,
)
from quant_replay_system.material_pit_evidence_gate_closure_plan_index import (
    build_material_pit_evidence_gate_closure_plan_index,
)
from quant_replay_system.material_pit_evidence_gate_closure_plan_status import (
    run_material_pit_evidence_gate_closure_plan_status,
)
from quant_replay_system.reviewer_material_evidence_fill_guidance import (
    build_reviewer_material_evidence_fill_guidance,
)
from quant_replay_system.reviewer_material_evidence_fill_guidance_health import (
    check_reviewer_material_evidence_fill_guidance_health,
)
from quant_replay_system.reviewer_material_evidence_fill_guidance_index import (
    build_reviewer_material_evidence_fill_guidance_index,
)
from quant_replay_system.reviewer_material_evidence_fill_guidance_status import (
    run_reviewer_material_evidence_fill_guidance_status,
)
from quant_replay_system.one_row_material_evidence_fill_package import (
    build_one_row_material_evidence_fill_package,
)
from quant_replay_system.one_row_material_evidence_fill_package_index import (
    build_one_row_material_evidence_fill_package_index,
)
from quant_replay_system.one_row_material_evidence_fill_package_health import (
    check_one_row_material_evidence_fill_package_health,
)
from quant_replay_system.one_row_material_evidence_fill_package_status import (
    run_one_row_material_evidence_fill_package_status,
)
from quant_replay_system.one_row_checklist_pass_candidate_preview import (
    build_one_row_checklist_pass_candidate_preview,
)
from quant_replay_system.one_row_checklist_pass_candidate_preview_health import (
    check_one_row_checklist_pass_candidate_preview_health,
)
from quant_replay_system.one_row_checklist_pass_candidate_preview_index import (
    build_one_row_checklist_pass_candidate_preview_index,
)
from quant_replay_system.one_row_checklist_pass_candidate_preview_status import (
    run_one_row_checklist_pass_candidate_preview_status,
)
from quant_replay_system.historical_replay_input_gate_validator import (
    run_historical_replay_input_gate_validator,
)
from quant_replay_system.historical_replay_input_gate_validator_health import (
    check_historical_replay_input_gate_validator_health,
)
from quant_replay_system.historical_replay_input_gate_validator_index import (
    build_historical_replay_input_gate_validator_index,
)
from quant_replay_system.historical_replay_input_gate_validator_status import (
    run_historical_replay_input_gate_validator_status,
)
from quant_replay_system.historical_replay_input_gate_validator_fixture import (
    build_historical_replay_input_gate_validator_fixture,
)
from quant_replay_system.historical_replay_input_gate_validator_fixture_health import (
    check_historical_replay_input_gate_validator_fixture_health,
)
from quant_replay_system.historical_replay_input_gate_validator_fixture_index import (
    build_historical_replay_input_gate_validator_fixture_index,
)
from quant_replay_system.historical_replay_input_gate_validator_fixture_status import (
    run_historical_replay_input_gate_validator_fixture_status,
)
from quant_replay_system.replay_substrate_schema_fixture import build_replay_substrate_schema_fixture
from quant_replay_system.replay_substrate_schema_fixture_health import (
    check_replay_substrate_schema_fixture_health,
)
from quant_replay_system.replay_substrate_schema_fixture_index import (
    build_replay_substrate_schema_fixture_index,
)
from quant_replay_system.replay_substrate_schema_fixture_status import (
    run_replay_substrate_schema_fixture_status,
)
from quant_replay_system.universe_profile_policy_audit import build_universe_profile_policy_audit
from quant_replay_system.universe_profile_policy_audit_health import check_universe_profile_policy_audit_health
from quant_replay_system.universe_profile_policy_audit_index import build_universe_profile_policy_audit_index
from quant_replay_system.universe_profile_policy_audit_status import run_universe_profile_policy_audit_status
from quant_replay_system.universe_profile_split_worklist_plan import build_universe_profile_split_worklist_plan
from quant_replay_system.universe_profile_split_worklist_plan_health import (
    check_universe_profile_split_worklist_plan_health,
)
from quant_replay_system.universe_profile_split_worklist_plan_index import (
    build_universe_profile_split_worklist_plan_index,
)
from quant_replay_system.universe_profile_split_worklist_plan_status import (
    run_universe_profile_split_worklist_plan_status,
)
from quant_replay_system.point_in_time_universe_overlay_review_health import (
    check_pit_universe_overlay_review_health,
)
from quant_replay_system.point_in_time_universe_overlay_review_index import (
    build_pit_universe_overlay_review_index,
)
from quant_replay_system.point_in_time_universe_overlay_review_status import (
    run_pit_universe_overlay_review_status,
)
from quant_replay_system.data import read_csv_preserve_symbol_columns
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
from quant_replay_system.historical_backfill import run_historical_backfill
from quant_replay_system.historical_backfill_health import check_historical_backfill_health
from quant_replay_system.historical_backfill_index import build_historical_backfill_index
from quant_replay_system.historical_backfill_status import run_historical_backfill_status
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
from quant_replay_system.market_cache_export import run_market_cache_export
from quant_replay_system.market_cache_export_health import check_market_cache_export_health
from quant_replay_system.market_cache_export_index import build_market_cache_export_index
from quant_replay_system.market_cache_export_policy_health import check_market_cache_export_policy_health
from quant_replay_system.market_cache_export_policy_index import build_market_cache_export_policy_index
from quant_replay_system.market_cache_export_policy import run_market_cache_export_policy_plan
from quant_replay_system.market_cache_export_policy_status import run_market_cache_export_policy_status
from quant_replay_system.market_cache_export_status import run_market_cache_export_status
from quant_replay_system.market_data_comparison import run_market_source_comparison
from quant_replay_system.market_cache_preflight import run_market_cache_preflight
from quant_replay_system.market_daily_update import run_market_daily_update
from quant_replay_system.market_daily_update import run_market_daily_update_manifest
from quant_replay_system.market_source_policy import run_market_source_policy_report
from quant_replay_system.market_update_handoff import run_market_update_snapshot_handoff
from quant_replay_system.market_update_handoff_health import check_market_update_handoff_health
from quant_replay_system.market_update_handoff_index import build_market_update_handoff_index
from quant_replay_system.market_update_handoff_status import run_market_update_handoff_status
from quant_replay_system.paper_artifact_health import check_paper_artifact_health
from quant_replay_system.paper_artifact_index import build_paper_artifact_index
from quant_replay_system.paper_reconciliation import reconcile_paper_fills
from quant_replay_system.paper_review import apply_paper_review_updates
from quant_replay_system.paper_review_template_health import check_review_template_health
from quant_replay_system.paper_workflow_status import run_paper_workflow_status
from quant_replay_system.replay_run import run_replay
from quant_replay_system.reviewed_replacement_worklist_plan import build_reviewed_replacement_worklist_plan
from quant_replay_system.reviewed_replacement_worklist_plan_health import check_reviewed_replacement_worklist_plan_health
from quant_replay_system.reviewed_replacement_worklist_plan_index import build_reviewed_replacement_worklist_plan_index
from quant_replay_system.reviewed_replacement_worklist_plan_status import run_reviewed_replacement_worklist_plan_status
from quant_replay_system.reviewed_replacement_worklist_acceptance import (
    build_reviewed_replacement_worklist_acceptance,
)
from quant_replay_system.reviewed_replacement_worklist_acceptance_health import (
    check_reviewed_replacement_worklist_acceptance_health,
)
from quant_replay_system.reviewed_replacement_worklist_acceptance_index import (
    build_reviewed_replacement_worklist_acceptance_index,
)
from quant_replay_system.reviewed_replacement_worklist_acceptance_status import (
    run_reviewed_replacement_worklist_acceptance_status,
)
from quant_replay_system.reviewed_replacement_worklist_activation import (
    build_reviewed_replacement_worklist_activation,
)
from quant_replay_system.reviewed_replacement_worklist_activation_health import (
    check_reviewed_replacement_worklist_activation_health,
)
from quant_replay_system.reviewed_replacement_worklist_activation_index import (
    build_reviewed_replacement_worklist_activation_index,
)
from quant_replay_system.reviewed_replacement_worklist_activation_status import (
    run_reviewed_replacement_worklist_activation_status,
)
from quant_replay_system.activated_replacement_worklist_evidence_update_plan import (
    build_activated_replacement_worklist_evidence_update_plan,
)
from quant_replay_system.activated_replacement_worklist_evidence_update_plan_health import (
    check_activated_replacement_worklist_evidence_update_plan_health,
)
from quant_replay_system.activated_replacement_worklist_evidence_update_plan_index import (
    build_activated_replacement_worklist_evidence_update_plan_index,
)
from quant_replay_system.activated_replacement_worklist_evidence_update_plan_status import (
    run_activated_replacement_worklist_evidence_update_plan_status,
)
from quant_replay_system.signal_advisory import build_signal_advisory_from_candidates
from quant_replay_system.signal_advisory_health import check_signal_advisory_health
from quant_replay_system.signal_advisory_index import build_signal_advisory_index
from quant_replay_system.signal_advisory_status import run_signal_advisory_status
from quant_replay_system.signal_semantics_health import check_signal_semantics_health
from quant_replay_system.signal_semantics_index import build_signal_semantics_index
from quant_replay_system.signal_semantics import run_signal_semantics
from quant_replay_system.signal_semantics_status import run_signal_semantics_status
from quant_replay_system.single_symbol_advisory import build_single_symbol_advisory
from quant_replay_system.single_symbol_advisory import build_single_symbol_advisory_answer
from quant_replay_system.single_symbol_advisory_answer_health import check_single_symbol_advisory_answer_health
from quant_replay_system.single_symbol_advisory_answer_index import build_single_symbol_advisory_answer_index
from quant_replay_system.single_symbol_advisory_answer_status import run_single_symbol_advisory_answer_status
from quant_replay_system.single_symbol_advisory_health import check_single_symbol_advisory_health
from quant_replay_system.single_symbol_advisory_index import build_single_symbol_advisory_index
from quant_replay_system.single_symbol_advisory_status import run_single_symbol_advisory_status
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

    current_backfill_plan = subparsers.add_parser(
        "current-candidates-backfill-plan",
        help="Plan local multi-date current-candidates backfill runs without executing them",
    )
    current_backfill_plan.add_argument("--cache-path", default="data/cache/market/daily_bars.csv", help="Local market cache CSV path")
    current_backfill_plan.add_argument("--start-date", required=True, help="Inclusive cache/signal planning start date")
    current_backfill_plan.add_argument("--end-date", required=True, help="Inclusive cache/signal planning end date")
    current_backfill_plan.add_argument("--universe", required=True, help="Universe name for planned current-candidates runs")
    current_backfill_plan.add_argument(
        "--selection-profile",
        choices=["default", "demo"],
        default="demo",
        help="Planned current-candidates selection profile; demo remains workflow validation only.",
    )
    current_backfill_plan.add_argument("--horizons", default="1,3,5,10", help="Comma-separated forward horizons")
    current_backfill_plan.add_argument("--max-dates", type=int, default=None, help="Maximum planned signal dates")
    current_backfill_plan.add_argument(
        "--warmup-trading-days",
        type=int,
        default=60,
        help="Required trading-day indicator warmup coverage through each planned signal date",
    )
    current_backfill_plan.add_argument("--min-symbol-coverage", type=int, default=4, help="Minimum distinct symbols per signal date")
    current_backfill_plan.add_argument("--source-policy", default="reviewed_local_v0", help="Reviewed source policy label")
    current_backfill_plan.add_argument("--output-dir", help="Optional backfill plan output directory")
    current_backfill_plan.set_defaults(handler=_handle_current_candidates_backfill_plan)

    current_backfill_plan_index = subparsers.add_parser(
        "current-candidates-backfill-plan-index",
        help="Build a local index of current-candidates backfill plan artifacts",
    )
    current_backfill_plan_index.add_argument("--root", default="outputs/reports/current_candidates_backfill_plan", help="Backfill plan artifact root")
    current_backfill_plan_index.add_argument("--output-dir", default="outputs/reports/current_candidates_backfill_plan/index", help="Index output directory")
    current_backfill_plan_index.add_argument("--include-missing-metadata", action="store_true", help="Include folders missing metadata.json")
    current_backfill_plan_index.set_defaults(handler=_handle_current_candidates_backfill_plan_index)

    current_backfill_plan_health = subparsers.add_parser(
        "current-candidates-backfill-plan-health",
        help="Check local current-candidates backfill plan artifact health",
    )
    current_backfill_plan_health.add_argument("--root", default="outputs/reports/current_candidates_backfill_plan", help="Backfill plan artifact root")
    current_backfill_plan_health.add_argument("--index", help="Optional backfill plan index CSV path")
    current_backfill_plan_health.add_argument("--output-dir", default="outputs/reports/current_candidates_backfill_plan/health", help="Health output directory")
    current_backfill_plan_health.set_defaults(handler=_handle_current_candidates_backfill_plan_health)

    current_backfill_plan_status = subparsers.add_parser(
        "current-candidates-backfill-plan-status",
        help="Summarize latest local current-candidates backfill plan status",
    )
    current_backfill_plan_status.add_argument("--root", default="outputs/reports/current_candidates_backfill_plan", help="Backfill plan artifact root")
    current_backfill_plan_status.add_argument("--output-dir", default="outputs/reports/current_candidates_backfill_plan/status", help="Status output directory")
    current_backfill_plan_status.set_defaults(handler=_handle_current_candidates_backfill_plan_status)

    current_backfill_execution_manifest = subparsers.add_parser(
        "current-candidates-backfill-execution-manifest",
        help="Build a manifest-only readiness review for planned multi-date current-candidates execution",
    )
    current_backfill_execution_manifest.add_argument("--plan", required=True, help="Current-candidates backfill plan CSV")
    current_backfill_execution_manifest.add_argument("--snapshot-root", default="outputs/reports/data_pipeline", help="Existing data-pipeline snapshot manifest root")
    current_backfill_execution_manifest.add_argument("--snapshot-quality-root", default="outputs/reports/snapshot_quality", help="Existing snapshot-quality artifact root")
    current_backfill_execution_manifest.add_argument("--universe-root", default="data/raw/LOCAL_CSV/universe_overlay", help="Reviewed universe overlay root")
    current_backfill_execution_manifest.add_argument(
        "--selection-profile",
        default=None,
        help="Optional reviewed selection profile label for the readiness manifest",
    )
    current_backfill_execution_manifest.add_argument(
        "--output-dir",
        default="outputs/reports/current_candidates_backfill_execution_manifest",
        help="Execution manifest output directory",
    )
    current_backfill_execution_manifest.set_defaults(handler=_handle_current_candidates_backfill_execution_manifest)

    pit_universe_overlay_plan = subparsers.add_parser(
        "pit-universe-overlay-plan",
        help="Build a plan-only point-in-time universe overlay review template from blocked execution manifest rows",
    )
    pit_universe_overlay_plan.add_argument(
        "--execution-manifest",
        required=True,
        help="Current-candidates backfill execution manifest CSV",
    )
    pit_universe_overlay_plan.add_argument(
        "--base-universe",
        default=None,
        help="Optional base universe CSV to derive manual-review template rows from",
    )
    pit_universe_overlay_plan.add_argument(
        "--universe-name",
        default="",
        help="Universe name to record in the overlay template",
    )
    pit_universe_overlay_plan.add_argument(
        "--allow-template-include",
        action="store_true",
        help="Prefill include_flag=true in the template while still requiring manual review",
    )
    pit_universe_overlay_plan.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_overlay_plan",
        help="PIT universe overlay plan output directory",
    )
    pit_universe_overlay_plan.set_defaults(handler=_handle_pit_universe_overlay_plan)

    pit_universe_overlay_plan_index = subparsers.add_parser(
        "pit-universe-overlay-plan-index",
        help="Build a local index of PIT universe overlay plan artifacts",
    )
    pit_universe_overlay_plan_index.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_overlay_plan",
        help="PIT universe overlay plan artifact root",
    )
    pit_universe_overlay_plan_index.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_overlay_plan/index",
        help="Index output directory",
    )
    pit_universe_overlay_plan_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Include folders missing metadata.json",
    )
    pit_universe_overlay_plan_index.set_defaults(handler=_handle_pit_universe_overlay_plan_index)

    pit_universe_overlay_plan_health = subparsers.add_parser(
        "pit-universe-overlay-plan-health",
        help="Check local PIT universe overlay plan artifact health",
    )
    pit_universe_overlay_plan_health.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_overlay_plan",
        help="PIT universe overlay plan artifact root",
    )
    pit_universe_overlay_plan_health.add_argument("--index", help="Optional PIT universe overlay plan index CSV path")
    pit_universe_overlay_plan_health.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_overlay_plan/health",
        help="Health output directory",
    )
    pit_universe_overlay_plan_health.set_defaults(handler=_handle_pit_universe_overlay_plan_health)

    pit_universe_overlay_plan_status = subparsers.add_parser(
        "pit-universe-overlay-plan-status",
        help="Summarize latest local PIT universe overlay plan status",
    )
    pit_universe_overlay_plan_status.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_overlay_plan",
        help="PIT universe overlay plan artifact root",
    )
    pit_universe_overlay_plan_status.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_overlay_plan/status",
        help="Status output directory",
    )
    pit_universe_overlay_plan_status.set_defaults(handler=_handle_pit_universe_overlay_plan_status)

    pit_universe_overlay_review = subparsers.add_parser(
        "pit-universe-overlay-review",
        help="Apply local reviewed PIT universe overlay updates without generating candidates or snapshots",
    )
    pit_universe_overlay_review.add_argument(
        "--overlay-plan",
        required=True,
        help="PIT universe overlay plan CSV",
    )
    pit_universe_overlay_review.add_argument(
        "--review-updates",
        default=None,
        help="Optional local PIT universe overlay review updates CSV",
    )
    pit_universe_overlay_review.add_argument(
        "--write-review-template-only",
        action="store_true",
        help="Write a reviewer update template and do not approve rows",
    )
    pit_universe_overlay_review.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_overlay_review",
        help="Reviewed PIT universe overlay output directory",
    )
    pit_universe_overlay_review.set_defaults(handler=_handle_pit_universe_overlay_review)

    pit_universe_overlay_review_index = subparsers.add_parser(
        "pit-universe-overlay-review-index",
        help="Build a local index of reviewed PIT universe overlay artifacts",
    )
    pit_universe_overlay_review_index.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_overlay_review",
        help="Reviewed PIT universe overlay artifact root",
    )
    pit_universe_overlay_review_index.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_overlay_review/index",
        help="Index output directory",
    )
    pit_universe_overlay_review_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Include folders missing metadata.json",
    )
    pit_universe_overlay_review_index.set_defaults(handler=_handle_pit_universe_overlay_review_index)

    pit_universe_overlay_review_health = subparsers.add_parser(
        "pit-universe-overlay-review-health",
        help="Check local reviewed PIT universe overlay artifact health",
    )
    pit_universe_overlay_review_health.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_overlay_review",
        help="Reviewed PIT universe overlay artifact root",
    )
    pit_universe_overlay_review_health.add_argument("--index", help="Optional reviewed PIT universe overlay index CSV path")
    pit_universe_overlay_review_health.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_overlay_review/health",
        help="Health output directory",
    )
    pit_universe_overlay_review_health.set_defaults(handler=_handle_pit_universe_overlay_review_health)

    pit_universe_overlay_review_status = subparsers.add_parser(
        "pit-universe-overlay-review-status",
        help="Summarize latest local reviewed PIT universe overlay status",
    )
    pit_universe_overlay_review_status.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_overlay_review",
        help="Reviewed PIT universe overlay artifact root",
    )
    pit_universe_overlay_review_status.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_overlay_review/status",
        help="Status output directory",
    )
    pit_universe_overlay_review_status.set_defaults(handler=_handle_pit_universe_overlay_review_status)

    pit_universe_overlay_export_readiness = subparsers.add_parser(
        "pit-universe-overlay-export-readiness",
        help="Check reviewed PIT universe rows for report-only export readiness",
    )
    pit_universe_overlay_export_readiness.add_argument(
        "--review",
        required=True,
        help="Reviewed PIT universe overlay CSV",
    )
    pit_universe_overlay_export_readiness.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_overlay_export_readiness",
        help="PIT universe overlay export readiness output directory",
    )
    pit_universe_overlay_export_readiness.set_defaults(handler=_handle_pit_universe_overlay_export_readiness)

    pit_universe_overlay_export_readiness_index = subparsers.add_parser(
        "pit-universe-overlay-export-readiness-index",
        help="Build a local index of PIT universe overlay export-readiness artifacts",
    )
    pit_universe_overlay_export_readiness_index.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_overlay_export_readiness",
        help="PIT universe overlay export-readiness artifact root",
    )
    pit_universe_overlay_export_readiness_index.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_overlay_export_readiness/index",
        help="Index output directory",
    )
    pit_universe_overlay_export_readiness_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Include folders missing metadata.json",
    )
    pit_universe_overlay_export_readiness_index.set_defaults(
        handler=_handle_pit_universe_overlay_export_readiness_index
    )

    pit_universe_overlay_export_readiness_health = subparsers.add_parser(
        "pit-universe-overlay-export-readiness-health",
        help="Check local PIT universe overlay export-readiness artifact health",
    )
    pit_universe_overlay_export_readiness_health.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_overlay_export_readiness",
        help="PIT universe overlay export-readiness artifact root",
    )
    pit_universe_overlay_export_readiness_health.add_argument(
        "--index",
        help="Optional PIT universe overlay export-readiness index CSV path",
    )
    pit_universe_overlay_export_readiness_health.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_overlay_export_readiness/health",
        help="Health output directory",
    )
    pit_universe_overlay_export_readiness_health.set_defaults(
        handler=_handle_pit_universe_overlay_export_readiness_health
    )

    pit_universe_overlay_export_readiness_status = subparsers.add_parser(
        "pit-universe-overlay-export-readiness-status",
        help="Summarize latest local PIT universe overlay export-readiness status",
    )
    pit_universe_overlay_export_readiness_status.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_overlay_export_readiness",
        help="PIT universe overlay export-readiness artifact root",
    )
    pit_universe_overlay_export_readiness_status.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_overlay_export_readiness/status",
        help="Status output directory",
    )
    pit_universe_overlay_export_readiness_status.set_defaults(
        handler=_handle_pit_universe_overlay_export_readiness_status
    )

    pit_universe_export_staging = subparsers.add_parser(
        "pit-universe-export-staging",
        help="Create guarded outputs-only PIT universe export staging artifacts",
    )
    pit_universe_export_staging.add_argument(
        "--export-readiness",
        required=True,
        help="PIT universe overlay export-readiness CSV",
    )
    pit_universe_export_staging.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_export_staging",
        help="PIT universe export staging output directory",
    )
    pit_universe_export_staging.add_argument(
        "--allow-diagnostic-source",
        action="store_true",
        help="Allow manual_diagnostics export-readiness sources for isolated diagnostics only",
    )
    pit_universe_export_staging.set_defaults(handler=_handle_pit_universe_export_staging)

    pit_universe_export_staging_index = subparsers.add_parser(
        "pit-universe-export-staging-index",
        help="Index guarded PIT universe export staging artifacts",
    )
    pit_universe_export_staging_index.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_export_staging",
        help="PIT universe export staging artifact root",
    )
    pit_universe_export_staging_index.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_export_staging/index",
        help="Index output directory",
    )
    pit_universe_export_staging_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Include staging folders that do not contain metadata.json",
    )
    pit_universe_export_staging_index.set_defaults(handler=_handle_pit_universe_export_staging_index)

    pit_universe_export_staging_health = subparsers.add_parser(
        "pit-universe-export-staging-health",
        help="Health-check guarded PIT universe export staging artifacts",
    )
    pit_universe_export_staging_health.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_export_staging",
        help="PIT universe export staging artifact root",
    )
    pit_universe_export_staging_health.add_argument(
        "--index",
        help="Optional PIT universe export staging index CSV",
    )
    pit_universe_export_staging_health.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_export_staging/health",
        help="Health output directory",
    )
    pit_universe_export_staging_health.set_defaults(handler=_handle_pit_universe_export_staging_health)

    pit_universe_export_staging_status = subparsers.add_parser(
        "pit-universe-export-staging-status",
        help="Summarize latest guarded PIT universe export staging status",
    )
    pit_universe_export_staging_status.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_export_staging",
        help="PIT universe export staging artifact root",
    )
    pit_universe_export_staging_status.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_export_staging/status",
        help="Status output directory",
    )
    pit_universe_export_staging_status.set_defaults(handler=_handle_pit_universe_export_staging_status)

    pit_universe_evidence_completion_helper = subparsers.add_parser(
        "pit-universe-evidence-completion-helper",
        help="Build report-only PIT universe evidence completion templates with non-authoritative hints",
    )
    pit_universe_evidence_completion_helper.add_argument(
        "--review",
        required=True,
        help="Reviewed PIT universe overlay CSV",
    )
    pit_universe_evidence_completion_helper.add_argument(
        "--base-universe",
        default=None,
        help="Optional base universe CSV for non-authoritative suggested_* hint fields",
    )
    pit_universe_evidence_completion_helper.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_evidence_completion_helper",
        help="PIT universe evidence completion helper output directory",
    )
    pit_universe_evidence_completion_helper.set_defaults(handler=_handle_pit_universe_evidence_completion_helper)

    pit_universe_evidence_review_worklist = subparsers.add_parser(
        "pit-universe-evidence-review-worklist",
        help="Build report-only PIT universe evidence review worklists from helper and review artifacts",
    )
    pit_universe_evidence_review_worklist.add_argument(
        "--helper",
        required=True,
        help="PIT universe evidence completion helper template CSV",
    )
    pit_universe_evidence_review_worklist.add_argument(
        "--review",
        required=True,
        help="Reviewed PIT universe overlay CSV",
    )
    pit_universe_evidence_review_worklist.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_evidence_review_worklist",
        help="PIT universe evidence review worklist output directory",
    )
    pit_universe_evidence_review_worklist.set_defaults(handler=_handle_pit_universe_evidence_review_worklist)

    pit_universe_evidence_review_worklist_index = subparsers.add_parser(
        "pit-universe-evidence-review-worklist-index",
        help="Build a local index of PIT universe evidence review worklist artifacts",
    )
    pit_universe_evidence_review_worklist_index.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_evidence_review_worklist",
        help="PIT universe evidence review worklist artifact root",
    )
    pit_universe_evidence_review_worklist_index.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_evidence_review_worklist/index",
        help="Index output directory",
    )
    pit_universe_evidence_review_worklist_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Include folders missing metadata.json",
    )
    pit_universe_evidence_review_worklist_index.set_defaults(
        handler=_handle_pit_universe_evidence_review_worklist_index
    )

    pit_universe_evidence_review_worklist_health = subparsers.add_parser(
        "pit-universe-evidence-review-worklist-health",
        help="Check local PIT universe evidence review worklist artifact health",
    )
    pit_universe_evidence_review_worklist_health.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_evidence_review_worklist",
        help="PIT universe evidence review worklist artifact root",
    )
    pit_universe_evidence_review_worklist_health.add_argument("--index", help="Optional worklist index CSV path")
    pit_universe_evidence_review_worklist_health.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_evidence_review_worklist/health",
        help="Health output directory",
    )
    pit_universe_evidence_review_worklist_health.set_defaults(
        handler=_handle_pit_universe_evidence_review_worklist_health
    )

    pit_universe_evidence_review_worklist_status = subparsers.add_parser(
        "pit-universe-evidence-review-worklist-status",
        help="Summarize latest local PIT universe evidence review worklist status",
    )
    pit_universe_evidence_review_worklist_status.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_evidence_review_worklist",
        help="PIT universe evidence review worklist artifact root",
    )
    pit_universe_evidence_review_worklist_status.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_evidence_review_worklist/status",
        help="Status output directory",
    )
    pit_universe_evidence_review_worklist_status.set_defaults(
        handler=_handle_pit_universe_evidence_review_worklist_status
    )

    pit_universe_evidence_update_ingestion = subparsers.add_parser(
        "pit-universe-evidence-update-ingestion",
        help="Validate reviewer-completed PIT universe evidence update CSVs under reports only",
    )
    pit_universe_evidence_update_ingestion.add_argument(
        "--completed-updates",
        required=True,
        help="Reviewer-completed PIT universe evidence update CSV",
    )
    pit_universe_evidence_update_ingestion.add_argument(
        "--worklist",
        default=None,
        help="Optional PIT universe evidence review worklist CSV for suggested_* hint cross-checks",
    )
    pit_universe_evidence_update_ingestion.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_evidence_update_ingestion",
        help="PIT universe evidence update ingestion output directory",
    )
    pit_universe_evidence_update_ingestion.set_defaults(
        handler=_handle_pit_universe_evidence_update_ingestion
    )

    pit_universe_evidence_update_ingestion_index = subparsers.add_parser(
        "pit-universe-evidence-update-ingestion-index",
        help="Build a local index of PIT universe evidence update ingestion artifacts",
    )
    pit_universe_evidence_update_ingestion_index.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_evidence_update_ingestion",
        help="PIT universe evidence update ingestion artifact root",
    )
    pit_universe_evidence_update_ingestion_index.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_evidence_update_ingestion/index",
        help="Index output directory",
    )
    pit_universe_evidence_update_ingestion_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Include folders missing metadata.json",
    )
    pit_universe_evidence_update_ingestion_index.set_defaults(
        handler=_handle_pit_universe_evidence_update_ingestion_index
    )

    pit_universe_evidence_update_ingestion_health = subparsers.add_parser(
        "pit-universe-evidence-update-ingestion-health",
        help="Check local PIT universe evidence update ingestion artifact health",
    )
    pit_universe_evidence_update_ingestion_health.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_evidence_update_ingestion",
        help="PIT universe evidence update ingestion artifact root",
    )
    pit_universe_evidence_update_ingestion_health.add_argument(
        "--index",
        help="Optional PIT universe evidence update ingestion index CSV path",
    )
    pit_universe_evidence_update_ingestion_health.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_evidence_update_ingestion/health",
        help="Health output directory",
    )
    pit_universe_evidence_update_ingestion_health.set_defaults(
        handler=_handle_pit_universe_evidence_update_ingestion_health
    )

    pit_universe_evidence_update_ingestion_status = subparsers.add_parser(
        "pit-universe-evidence-update-ingestion-status",
        help="Summarize latest local PIT universe evidence update ingestion status",
    )
    pit_universe_evidence_update_ingestion_status.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_evidence_update_ingestion",
        help="PIT universe evidence update ingestion artifact root",
    )
    pit_universe_evidence_update_ingestion_status.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_evidence_update_ingestion/status",
        help="Status output directory",
    )
    pit_universe_evidence_update_ingestion_status.set_defaults(
        handler=_handle_pit_universe_evidence_update_ingestion_status
    )

    pit_evidence_checklist_validator = subparsers.add_parser(
        "pit-evidence-checklist-validator",
        help="Validate PIT evidence updates against the strict checklist under reports only",
    )
    pit_evidence_checklist_validator.add_argument("--completed-updates", required=True)
    pit_evidence_checklist_validator.add_argument("--stock-checklist", required=True)
    pit_evidence_checklist_validator.add_argument("--etf-checklist", required=True)
    pit_evidence_checklist_validator.add_argument("--source-acceptance", default=None)
    pit_evidence_checklist_validator.add_argument(
        "--output-dir",
        default="outputs/reports/pit_evidence_checklist_validator",
    )
    pit_evidence_checklist_validator.set_defaults(handler=_handle_pit_evidence_checklist_validator)

    pit_evidence_checklist_validator_index = subparsers.add_parser(
        "pit-evidence-checklist-validator-index",
        help="Build a local index of PIT evidence checklist validator artifacts",
    )
    pit_evidence_checklist_validator_index.add_argument(
        "--root",
        default="outputs/reports/pit_evidence_checklist_validator",
    )
    pit_evidence_checklist_validator_index.add_argument(
        "--output-dir",
        default="outputs/reports/pit_evidence_checklist_validator/index",
    )
    pit_evidence_checklist_validator_index.set_defaults(handler=_handle_pit_evidence_checklist_validator_index)

    pit_evidence_checklist_validator_health = subparsers.add_parser(
        "pit-evidence-checklist-validator-health",
        help="Check local PIT evidence checklist validator artifact health",
    )
    pit_evidence_checklist_validator_health.add_argument(
        "--root",
        default="outputs/reports/pit_evidence_checklist_validator",
    )
    pit_evidence_checklist_validator_health.add_argument(
        "--output-dir",
        default="outputs/reports/pit_evidence_checklist_validator/health",
    )
    pit_evidence_checklist_validator_health.set_defaults(handler=_handle_pit_evidence_checklist_validator_health)

    pit_evidence_checklist_validator_status = subparsers.add_parser(
        "pit-evidence-checklist-validator-status",
        help="Summarize latest PIT evidence checklist validator status",
    )
    pit_evidence_checklist_validator_status.add_argument(
        "--root",
        default="outputs/reports/pit_evidence_checklist_validator",
    )
    pit_evidence_checklist_validator_status.add_argument(
        "--output-dir",
        default="outputs/reports/pit_evidence_checklist_validator/status",
    )
    pit_evidence_checklist_validator_status.set_defaults(handler=_handle_pit_evidence_checklist_validator_status)

    pit_evidence_policy_profile_comparison = subparsers.add_parser(
        "pit-evidence-policy-profile-comparison",
        help="Compare strict PIT evidence validation with an opt-in policy profile under reports only",
    )
    pit_evidence_policy_profile_comparison.add_argument("--validator", required=True)
    pit_evidence_policy_profile_comparison.add_argument("--completed-updates", required=True)
    pit_evidence_policy_profile_comparison.add_argument("--policy-audit", required=True)
    pit_evidence_policy_profile_comparison.add_argument("--profile", default="EOD_POST_CLOSE_LOW_BUDGET_PIT")
    pit_evidence_policy_profile_comparison.add_argument("--decision-policy", default="EOD_POST_CLOSE")
    pit_evidence_policy_profile_comparison.add_argument("--decision-time")
    pit_evidence_policy_profile_comparison.add_argument(
        "--output-dir",
        default="outputs/reports/pit_evidence_policy_profile_comparison",
    )
    pit_evidence_policy_profile_comparison.set_defaults(handler=_handle_pit_evidence_policy_profile_comparison)

    pit_evidence_policy_profile_comparison_index = subparsers.add_parser(
        "pit-evidence-policy-profile-comparison-index",
        help="Build a local index of PIT evidence policy profile comparison artifacts",
    )
    pit_evidence_policy_profile_comparison_index.add_argument(
        "--root",
        default="outputs/reports/pit_evidence_policy_profile_comparison",
    )
    pit_evidence_policy_profile_comparison_index.add_argument(
        "--output-dir",
        default="outputs/reports/pit_evidence_policy_profile_comparison/index",
    )
    pit_evidence_policy_profile_comparison_index.set_defaults(
        handler=_handle_pit_evidence_policy_profile_comparison_index
    )

    pit_evidence_policy_profile_comparison_health = subparsers.add_parser(
        "pit-evidence-policy-profile-comparison-health",
        help="Check local PIT evidence policy profile comparison artifact health",
    )
    pit_evidence_policy_profile_comparison_health.add_argument(
        "--root",
        default="outputs/reports/pit_evidence_policy_profile_comparison",
    )
    pit_evidence_policy_profile_comparison_health.add_argument(
        "--output-dir",
        default="outputs/reports/pit_evidence_policy_profile_comparison/health",
    )
    pit_evidence_policy_profile_comparison_health.set_defaults(
        handler=_handle_pit_evidence_policy_profile_comparison_health
    )

    pit_evidence_policy_profile_comparison_status = subparsers.add_parser(
        "pit-evidence-policy-profile-comparison-status",
        help="Summarize latest PIT evidence policy profile comparison status",
    )
    pit_evidence_policy_profile_comparison_status.add_argument(
        "--root",
        default="outputs/reports/pit_evidence_policy_profile_comparison",
    )
    pit_evidence_policy_profile_comparison_status.add_argument(
        "--output-dir",
        default="outputs/reports/pit_evidence_policy_profile_comparison/status",
    )
    pit_evidence_policy_profile_comparison_status.set_defaults(
        handler=_handle_pit_evidence_policy_profile_comparison_status
    )

    pit_official_status_evidence_packet = subparsers.add_parser(
        "pit-official-status-evidence-packet",
        help="Build report-only PIT official status evidence packets for first-batch evidence rows",
    )
    pit_official_status_evidence_packet.add_argument(
        "--source-smoke-root",
        default="outputs/reports/manual_diagnostics/szse_status_source_access_smoke_v0_1",
    )
    pit_official_status_evidence_packet.add_argument(
        "--non-relaxed-root",
        default="outputs/reports/manual_diagnostics/codex_non_relaxed_pit_evidence_gap_acquisition_v0_1",
    )
    pit_official_status_evidence_packet.add_argument(
        "--policy-comparison",
        default="outputs/reports/pit_evidence_policy_profile_comparison/0ef6d2f3bae6",
    )
    pit_official_status_evidence_packet.add_argument(
        "--validator",
        default="outputs/reports/pit_evidence_checklist_validator/62e9eb747197",
    )
    pit_official_status_evidence_packet.add_argument(
        "--activated-plan",
        default="outputs/reports/activated_replacement_worklist_evidence_update_plan/4e268d67bd7d",
    )
    pit_official_status_evidence_packet.add_argument(
        "--stock-checklist",
        default="outputs/reports/manual_diagnostics/pit_strict_evidence_checklist_v0_3/stock_core_strict_evidence_checklist.csv",
    )
    pit_official_status_evidence_packet.add_argument(
        "--etf-checklist",
        default="outputs/reports/manual_diagnostics/pit_strict_evidence_checklist_v0_3/etf_core_strict_evidence_checklist.csv",
    )
    pit_official_status_evidence_packet.add_argument(
        "--source-acceptance",
        default="outputs/reports/manual_diagnostics/pit_strict_evidence_checklist_v0_3/source_acceptance_matrix.csv",
    )
    pit_official_status_evidence_packet.add_argument(
        "--output-dir",
        default="outputs/reports/pit_official_status_evidence_packet",
    )
    pit_official_status_evidence_packet.set_defaults(handler=_handle_pit_official_status_evidence_packet)

    pit_official_status_evidence_packet_index = subparsers.add_parser(
        "pit-official-status-evidence-packet-index",
        help="Build a local index of PIT official status evidence packet artifacts",
    )
    pit_official_status_evidence_packet_index.add_argument(
        "--root",
        default="outputs/reports/pit_official_status_evidence_packet",
    )
    pit_official_status_evidence_packet_index.add_argument(
        "--output-dir",
        default="outputs/reports/pit_official_status_evidence_packet/index",
    )
    pit_official_status_evidence_packet_index.set_defaults(
        handler=_handle_pit_official_status_evidence_packet_index
    )

    pit_official_status_evidence_packet_health = subparsers.add_parser(
        "pit-official-status-evidence-packet-health",
        help="Check local PIT official status evidence packet artifact health",
    )
    pit_official_status_evidence_packet_health.add_argument(
        "--root",
        default="outputs/reports/pit_official_status_evidence_packet",
    )
    pit_official_status_evidence_packet_health.add_argument(
        "--output-dir",
        default="outputs/reports/pit_official_status_evidence_packet/health",
    )
    pit_official_status_evidence_packet_health.set_defaults(
        handler=_handle_pit_official_status_evidence_packet_health
    )

    pit_official_status_evidence_packet_status = subparsers.add_parser(
        "pit-official-status-evidence-packet-status",
        help="Summarize latest PIT official status evidence packet status",
    )
    pit_official_status_evidence_packet_status.add_argument(
        "--root",
        default="outputs/reports/pit_official_status_evidence_packet",
    )
    pit_official_status_evidence_packet_status.add_argument(
        "--output-dir",
        default="outputs/reports/pit_official_status_evidence_packet/status",
    )
    pit_official_status_evidence_packet_status.set_defaults(
        handler=_handle_pit_official_status_evidence_packet_status
    )

    pit_official_status_evidence_packet_enrichment = subparsers.add_parser(
        "pit-official-status-evidence-packet-enrichment",
        help="Enrich PIT official status evidence packets with quotation and reviewed no-hit context",
    )
    pit_official_status_evidence_packet_enrichment.add_argument(
        "--packet",
        default="outputs/reports/pit_official_status_evidence_packet/8efabe2ffe62",
    )
    pit_official_status_evidence_packet_enrichment.add_argument(
        "--quotation-probe",
        default="outputs/reports/manual_diagnostics/szse_1815_same_date_quotation_probe_v0_1",
    )
    pit_official_status_evidence_packet_enrichment.add_argument(
        "--policy-comparison",
        default="outputs/reports/pit_evidence_policy_profile_comparison/c1a75d1091c6",
    )
    pit_official_status_evidence_packet_enrichment.add_argument(
        "--output-dir",
        default="outputs/reports/pit_official_status_evidence_packet_enrichment",
    )
    pit_official_status_evidence_packet_enrichment.set_defaults(
        handler=_handle_pit_official_status_evidence_packet_enrichment
    )

    pit_official_status_evidence_packet_enrichment_index = subparsers.add_parser(
        "pit-official-status-evidence-packet-enrichment-index",
        help="Build a local index of PIT official status evidence packet enrichment artifacts",
    )
    pit_official_status_evidence_packet_enrichment_index.add_argument(
        "--root",
        default="outputs/reports/pit_official_status_evidence_packet_enrichment",
    )
    pit_official_status_evidence_packet_enrichment_index.add_argument(
        "--output-dir",
        default="outputs/reports/pit_official_status_evidence_packet_enrichment/index",
    )
    pit_official_status_evidence_packet_enrichment_index.set_defaults(
        handler=_handle_pit_official_status_evidence_packet_enrichment_index
    )

    pit_official_status_evidence_packet_enrichment_health = subparsers.add_parser(
        "pit-official-status-evidence-packet-enrichment-health",
        help="Check local PIT official status evidence packet enrichment artifact health",
    )
    pit_official_status_evidence_packet_enrichment_health.add_argument(
        "--root",
        default="outputs/reports/pit_official_status_evidence_packet_enrichment",
    )
    pit_official_status_evidence_packet_enrichment_health.add_argument(
        "--output-dir",
        default="outputs/reports/pit_official_status_evidence_packet_enrichment/health",
    )
    pit_official_status_evidence_packet_enrichment_health.set_defaults(
        handler=_handle_pit_official_status_evidence_packet_enrichment_health
    )

    pit_official_status_evidence_packet_enrichment_status = subparsers.add_parser(
        "pit-official-status-evidence-packet-enrichment-status",
        help="Summarize latest PIT official status evidence packet enrichment status",
    )
    pit_official_status_evidence_packet_enrichment_status.add_argument(
        "--root",
        default="outputs/reports/pit_official_status_evidence_packet_enrichment",
    )
    pit_official_status_evidence_packet_enrichment_status.add_argument(
        "--output-dir",
        default="outputs/reports/pit_official_status_evidence_packet_enrichment/status",
    )
    pit_official_status_evidence_packet_enrichment_status.set_defaults(
        handler=_handle_pit_official_status_evidence_packet_enrichment_status
    )

    reviewer_no_hit_acceptance = subparsers.add_parser(
        "reviewer-no-hit-source-coverage-acceptance",
        help="Create report-only reviewer no-hit source coverage acceptance templates",
    )
    reviewer_no_hit_acceptance.add_argument(
        "--enrichment",
        default="outputs/reports/pit_official_status_evidence_packet_enrichment/cb5f323d3c8c",
    )
    reviewer_no_hit_acceptance.add_argument(
        "--audit",
        default="outputs/reports/manual_diagnostics/reviewer_no_hit_source_coverage_acceptance_audit_v0_1",
    )
    reviewer_no_hit_acceptance.add_argument(
        "--policy-comparison",
        default="outputs/reports/pit_evidence_policy_profile_comparison/c1a75d1091c6",
    )
    reviewer_no_hit_acceptance.add_argument("--reviewer-acceptance", default=None)
    reviewer_no_hit_acceptance.add_argument(
        "--output-dir",
        default="outputs/reports/reviewer_no_hit_source_coverage_acceptance",
    )
    reviewer_no_hit_acceptance.set_defaults(handler=_handle_reviewer_no_hit_source_coverage_acceptance)

    reviewer_no_hit_acceptance_index = subparsers.add_parser(
        "reviewer-no-hit-source-coverage-acceptance-index",
        help="Build a local index of reviewer no-hit source coverage acceptance artifacts",
    )
    reviewer_no_hit_acceptance_index.add_argument(
        "--root",
        default="outputs/reports/reviewer_no_hit_source_coverage_acceptance",
    )
    reviewer_no_hit_acceptance_index.add_argument(
        "--output-dir",
        default="outputs/reports/reviewer_no_hit_source_coverage_acceptance/index",
    )
    reviewer_no_hit_acceptance_index.set_defaults(handler=_handle_reviewer_no_hit_source_coverage_acceptance_index)

    reviewer_no_hit_acceptance_health = subparsers.add_parser(
        "reviewer-no-hit-source-coverage-acceptance-health",
        help="Check reviewer no-hit source coverage acceptance artifact health",
    )
    reviewer_no_hit_acceptance_health.add_argument(
        "--root",
        default="outputs/reports/reviewer_no_hit_source_coverage_acceptance",
    )
    reviewer_no_hit_acceptance_health.add_argument(
        "--output-dir",
        default="outputs/reports/reviewer_no_hit_source_coverage_acceptance/health",
    )
    reviewer_no_hit_acceptance_health.set_defaults(handler=_handle_reviewer_no_hit_source_coverage_acceptance_health)

    reviewer_no_hit_acceptance_status = subparsers.add_parser(
        "reviewer-no-hit-source-coverage-acceptance-status",
        help="Summarize latest reviewer no-hit source coverage acceptance status",
    )
    reviewer_no_hit_acceptance_status.add_argument(
        "--root",
        default="outputs/reports/reviewer_no_hit_source_coverage_acceptance",
    )
    reviewer_no_hit_acceptance_status.add_argument(
        "--output-dir",
        default="outputs/reports/reviewer_no_hit_source_coverage_acceptance/status",
    )
    reviewer_no_hit_acceptance_status.set_defaults(handler=_handle_reviewer_no_hit_source_coverage_acceptance_status)

    reviewer_no_hit_downstream_impact = subparsers.add_parser(
        "reviewer-no-hit-acceptance-downstream-impact",
        help="Create report-only downstream impact views for reviewer no-hit acceptance context",
    )
    reviewer_no_hit_downstream_impact.add_argument(
        "--acceptance",
        default="outputs/reports/reviewer_no_hit_source_coverage_acceptance/2e05e4b74794",
    )
    reviewer_no_hit_downstream_impact.add_argument(
        "--enrichment",
        default="outputs/reports/pit_official_status_evidence_packet_enrichment/cb5f323d3c8c",
    )
    reviewer_no_hit_downstream_impact.add_argument(
        "--validator",
        default="outputs/reports/pit_evidence_checklist_validator/62e9eb747197",
    )
    reviewer_no_hit_downstream_impact.add_argument(
        "--policy-comparison",
        default="outputs/reports/pit_evidence_policy_profile_comparison/c1a75d1091c6",
    )
    reviewer_no_hit_downstream_impact.add_argument(
        "--output-dir",
        default="outputs/reports/reviewer_no_hit_acceptance_downstream_impact",
    )
    reviewer_no_hit_downstream_impact.set_defaults(handler=_handle_reviewer_no_hit_acceptance_downstream_impact)

    reviewer_no_hit_downstream_impact_index = subparsers.add_parser(
        "reviewer-no-hit-acceptance-downstream-impact-index",
        help="Build a local index of reviewer no-hit acceptance downstream impact artifacts",
    )
    reviewer_no_hit_downstream_impact_index.add_argument(
        "--root",
        default="outputs/reports/reviewer_no_hit_acceptance_downstream_impact",
    )
    reviewer_no_hit_downstream_impact_index.add_argument(
        "--output-dir",
        default="outputs/reports/reviewer_no_hit_acceptance_downstream_impact/index",
    )
    reviewer_no_hit_downstream_impact_index.set_defaults(
        handler=_handle_reviewer_no_hit_acceptance_downstream_impact_index
    )

    reviewer_no_hit_downstream_impact_health = subparsers.add_parser(
        "reviewer-no-hit-acceptance-downstream-impact-health",
        help="Check reviewer no-hit acceptance downstream impact artifact health",
    )
    reviewer_no_hit_downstream_impact_health.add_argument(
        "--root",
        default="outputs/reports/reviewer_no_hit_acceptance_downstream_impact",
    )
    reviewer_no_hit_downstream_impact_health.add_argument(
        "--output-dir",
        default="outputs/reports/reviewer_no_hit_acceptance_downstream_impact/health",
    )
    reviewer_no_hit_downstream_impact_health.set_defaults(
        handler=_handle_reviewer_no_hit_acceptance_downstream_impact_health
    )

    reviewer_no_hit_downstream_impact_status = subparsers.add_parser(
        "reviewer-no-hit-acceptance-downstream-impact-status",
        help="Summarize latest reviewer no-hit acceptance downstream impact status",
    )
    reviewer_no_hit_downstream_impact_status.add_argument(
        "--root",
        default="outputs/reports/reviewer_no_hit_acceptance_downstream_impact",
    )
    reviewer_no_hit_downstream_impact_status.add_argument(
        "--output-dir",
        default="outputs/reports/reviewer_no_hit_acceptance_downstream_impact/status",
    )
    reviewer_no_hit_downstream_impact_status.set_defaults(
        handler=_handle_reviewer_no_hit_acceptance_downstream_impact_status
    )

    first_batch_completion_plan = subparsers.add_parser(
        "first-batch-reviewer-evidence-completion-plan",
        help="Create a report-only first-batch reviewer evidence completion plan",
    )
    first_batch_completion_plan.add_argument(
        "--evidence-update-plan",
        default="outputs/reports/activated_replacement_worklist_evidence_update_plan/4e268d67bd7d",
    )
    first_batch_completion_plan.add_argument(
        "--downstream-impact",
        default="outputs/reports/reviewer_no_hit_acceptance_downstream_impact/9e164963455e",
    )
    first_batch_completion_plan.add_argument(
        "--enrichment",
        default="outputs/reports/pit_official_status_evidence_packet_enrichment/cb5f323d3c8c",
    )
    first_batch_completion_plan.add_argument(
        "--validator",
        default="outputs/reports/pit_evidence_checklist_validator/62e9eb747197",
    )
    first_batch_completion_plan.add_argument(
        "--policy-comparison",
        default="outputs/reports/pit_evidence_policy_profile_comparison/c1a75d1091c6",
    )
    first_batch_completion_plan.add_argument(
        "--output-dir",
        default="outputs/reports/first_batch_reviewer_evidence_completion_plan",
    )
    first_batch_completion_plan.set_defaults(handler=_handle_first_batch_reviewer_evidence_completion_plan)

    first_batch_completion_plan_index = subparsers.add_parser(
        "first-batch-reviewer-evidence-completion-plan-index",
        help="Build a local index of first-batch reviewer evidence completion plans",
    )
    first_batch_completion_plan_index.add_argument(
        "--root",
        default="outputs/reports/first_batch_reviewer_evidence_completion_plan",
    )
    first_batch_completion_plan_index.add_argument(
        "--output-dir",
        default="outputs/reports/first_batch_reviewer_evidence_completion_plan/index",
    )
    first_batch_completion_plan_index.set_defaults(handler=_handle_first_batch_reviewer_evidence_completion_plan_index)

    first_batch_completion_plan_health = subparsers.add_parser(
        "first-batch-reviewer-evidence-completion-plan-health",
        help="Check first-batch reviewer evidence completion plan health",
    )
    first_batch_completion_plan_health.add_argument(
        "--root",
        default="outputs/reports/first_batch_reviewer_evidence_completion_plan",
    )
    first_batch_completion_plan_health.add_argument(
        "--output-dir",
        default="outputs/reports/first_batch_reviewer_evidence_completion_plan/health",
    )
    first_batch_completion_plan_health.set_defaults(handler=_handle_first_batch_reviewer_evidence_completion_plan_health)

    first_batch_completion_plan_status = subparsers.add_parser(
        "first-batch-reviewer-evidence-completion-plan-status",
        help="Summarize latest first-batch reviewer evidence completion plan status",
    )
    first_batch_completion_plan_status.add_argument(
        "--root",
        default="outputs/reports/first_batch_reviewer_evidence_completion_plan",
    )
    first_batch_completion_plan_status.add_argument(
        "--output-dir",
        default="outputs/reports/first_batch_reviewer_evidence_completion_plan/status",
    )
    first_batch_completion_plan_status.set_defaults(handler=_handle_first_batch_reviewer_evidence_completion_plan_status)

    first_batch_partial_completion_impact = subparsers.add_parser(
        "first-batch-partial-completion-impact",
        help="Compare partial first-batch reviewer completion fixtures against the completion plan",
    )
    first_batch_partial_completion_impact.add_argument(
        "--completion-plan",
        default="outputs/reports/first_batch_reviewer_evidence_completion_plan/c630522f235a",
    )
    first_batch_partial_completion_impact.add_argument(
        "--partial-completion",
        default=None,
        help="Optional partial reviewer completion fixture CSV",
    )
    first_batch_partial_completion_impact.add_argument(
        "--output-dir",
        default="outputs/reports/first_batch_partial_completion_impact",
    )
    first_batch_partial_completion_impact.set_defaults(handler=_handle_first_batch_partial_completion_impact)

    first_batch_partial_completion_impact_index = subparsers.add_parser(
        "first-batch-partial-completion-impact-index",
        help="Build a local index of first-batch partial completion impact artifacts",
    )
    first_batch_partial_completion_impact_index.add_argument(
        "--root",
        default="outputs/reports/first_batch_partial_completion_impact",
    )
    first_batch_partial_completion_impact_index.add_argument(
        "--output-dir",
        default="outputs/reports/first_batch_partial_completion_impact/index",
    )
    first_batch_partial_completion_impact_index.set_defaults(
        handler=_handle_first_batch_partial_completion_impact_index
    )

    first_batch_partial_completion_impact_health = subparsers.add_parser(
        "first-batch-partial-completion-impact-health",
        help="Check first-batch partial completion impact artifact health",
    )
    first_batch_partial_completion_impact_health.add_argument(
        "--root",
        default="outputs/reports/first_batch_partial_completion_impact",
    )
    first_batch_partial_completion_impact_health.add_argument(
        "--output-dir",
        default="outputs/reports/first_batch_partial_completion_impact/health",
    )
    first_batch_partial_completion_impact_health.set_defaults(
        handler=_handle_first_batch_partial_completion_impact_health
    )

    first_batch_partial_completion_impact_status = subparsers.add_parser(
        "first-batch-partial-completion-impact-status",
        help="Summarize latest first-batch partial completion impact status",
    )
    first_batch_partial_completion_impact_status.add_argument(
        "--root",
        default="outputs/reports/first_batch_partial_completion_impact",
    )
    first_batch_partial_completion_impact_status.add_argument(
        "--output-dir",
        default="outputs/reports/first_batch_partial_completion_impact/status",
    )
    first_batch_partial_completion_impact_status.set_defaults(
        handler=_handle_first_batch_partial_completion_impact_status
    )

    material_pit_gate_closure_plan = subparsers.add_parser(
        "material-pit-evidence-gate-closure-plan",
        help="Create report-only material PIT evidence gate closure plans and fill templates",
    )
    material_pit_gate_closure_plan.add_argument(
        "--audit",
        default="outputs/reports/manual_diagnostics/material_pit_evidence_gate_closure_planning_audit_v0_1",
    )
    material_pit_gate_closure_plan.add_argument(
        "--partial-impact",
        default="outputs/reports/first_batch_partial_completion_impact/ea81f81ae764",
    )
    material_pit_gate_closure_plan.add_argument(
        "--completion-plan",
        default="outputs/reports/first_batch_reviewer_evidence_completion_plan/c630522f235a",
    )
    material_pit_gate_closure_plan.add_argument(
        "--validator",
        default="outputs/reports/pit_evidence_checklist_validator/62e9eb747197",
    )
    material_pit_gate_closure_plan.add_argument(
        "--policy-comparison",
        default="outputs/reports/pit_evidence_policy_profile_comparison/c1a75d1091c6",
    )
    material_pit_gate_closure_plan.add_argument(
        "--enrichment",
        default="outputs/reports/pit_official_status_evidence_packet_enrichment/cb5f323d3c8c",
    )
    material_pit_gate_closure_plan.add_argument(
        "--reviewer-no-hit-acceptance",
        default="outputs/reports/reviewer_no_hit_source_coverage_acceptance/2e05e4b74794",
    )
    material_pit_gate_closure_plan.add_argument(
        "--reviewer-no-hit-downstream-impact",
        default="outputs/reports/reviewer_no_hit_acceptance_downstream_impact/9e164963455e",
    )
    material_pit_gate_closure_plan.add_argument(
        "--output-dir",
        default="outputs/reports/material_pit_evidence_gate_closure_plan",
    )
    material_pit_gate_closure_plan.set_defaults(handler=_handle_material_pit_evidence_gate_closure_plan)

    material_pit_gate_closure_plan_index = subparsers.add_parser(
        "material-pit-evidence-gate-closure-plan-index",
        help="Build a local index of material PIT evidence gate closure plan artifacts",
    )
    material_pit_gate_closure_plan_index.add_argument(
        "--root",
        default="outputs/reports/material_pit_evidence_gate_closure_plan",
    )
    material_pit_gate_closure_plan_index.add_argument(
        "--output-dir",
        default="outputs/reports/material_pit_evidence_gate_closure_plan/index",
    )
    material_pit_gate_closure_plan_index.set_defaults(
        handler=_handle_material_pit_evidence_gate_closure_plan_index
    )

    material_pit_gate_closure_plan_health = subparsers.add_parser(
        "material-pit-evidence-gate-closure-plan-health",
        help="Check material PIT evidence gate closure plan artifact health",
    )
    material_pit_gate_closure_plan_health.add_argument(
        "--root",
        default="outputs/reports/material_pit_evidence_gate_closure_plan",
    )
    material_pit_gate_closure_plan_health.add_argument(
        "--output-dir",
        default="outputs/reports/material_pit_evidence_gate_closure_plan/health",
    )
    material_pit_gate_closure_plan_health.set_defaults(
        handler=_handle_material_pit_evidence_gate_closure_plan_health
    )

    material_pit_gate_closure_plan_status = subparsers.add_parser(
        "material-pit-evidence-gate-closure-plan-status",
        help="Summarize latest material PIT evidence gate closure plan status",
    )
    material_pit_gate_closure_plan_status.add_argument(
        "--root",
        default="outputs/reports/material_pit_evidence_gate_closure_plan",
    )
    material_pit_gate_closure_plan_status.add_argument(
        "--output-dir",
        default="outputs/reports/material_pit_evidence_gate_closure_plan/status",
    )
    material_pit_gate_closure_plan_status.set_defaults(
        handler=_handle_material_pit_evidence_gate_closure_plan_status
    )

    reviewer_material_evidence_fill_guidance = subparsers.add_parser(
        "reviewer-material-evidence-fill-guidance",
        help="Create report-only reviewer material evidence fill guidance from a material PIT gate closure plan",
    )
    reviewer_material_evidence_fill_guidance.add_argument(
        "--material-plan",
        default="outputs/reports/material_pit_evidence_gate_closure_plan/2d6ab8e7f9f8",
    )
    reviewer_material_evidence_fill_guidance.add_argument(
        "--audit",
        default="outputs/reports/manual_diagnostics/reviewer_material_evidence_fill_guidance_audit_v0_1",
    )
    reviewer_material_evidence_fill_guidance.add_argument(
        "--completion-plan",
        default="outputs/reports/first_batch_reviewer_evidence_completion_plan/c630522f235a",
    )
    reviewer_material_evidence_fill_guidance.add_argument(
        "--partial-impact",
        default="outputs/reports/first_batch_partial_completion_impact/ea81f81ae764",
    )
    reviewer_material_evidence_fill_guidance.add_argument(
        "--validator",
        default="outputs/reports/pit_evidence_checklist_validator/62e9eb747197",
    )
    reviewer_material_evidence_fill_guidance.add_argument(
        "--enrichment",
        default="outputs/reports/pit_official_status_evidence_packet_enrichment/cb5f323d3c8c",
    )
    reviewer_material_evidence_fill_guidance.add_argument(
        "--reviewer-no-hit-acceptance",
        default="outputs/reports/reviewer_no_hit_source_coverage_acceptance/2e05e4b74794",
    )
    reviewer_material_evidence_fill_guidance.add_argument(
        "--reviewer-no-hit-downstream-impact",
        default="outputs/reports/reviewer_no_hit_acceptance_downstream_impact/9e164963455e",
    )
    reviewer_material_evidence_fill_guidance.add_argument(
        "--output-dir",
        default="outputs/reports/reviewer_material_evidence_fill_guidance",
    )
    reviewer_material_evidence_fill_guidance.set_defaults(
        handler=_handle_reviewer_material_evidence_fill_guidance
    )

    reviewer_material_evidence_fill_guidance_index = subparsers.add_parser(
        "reviewer-material-evidence-fill-guidance-index",
        help="Build a local index of reviewer material evidence fill guidance artifacts",
    )
    reviewer_material_evidence_fill_guidance_index.add_argument(
        "--root",
        default="outputs/reports/reviewer_material_evidence_fill_guidance",
    )
    reviewer_material_evidence_fill_guidance_index.add_argument(
        "--output-dir",
        default="outputs/reports/reviewer_material_evidence_fill_guidance/index",
    )
    reviewer_material_evidence_fill_guidance_index.set_defaults(
        handler=_handle_reviewer_material_evidence_fill_guidance_index
    )

    reviewer_material_evidence_fill_guidance_health = subparsers.add_parser(
        "reviewer-material-evidence-fill-guidance-health",
        help="Check reviewer material evidence fill guidance artifact health",
    )
    reviewer_material_evidence_fill_guidance_health.add_argument(
        "--root",
        default="outputs/reports/reviewer_material_evidence_fill_guidance",
    )
    reviewer_material_evidence_fill_guidance_health.add_argument(
        "--output-dir",
        default="outputs/reports/reviewer_material_evidence_fill_guidance/health",
    )
    reviewer_material_evidence_fill_guidance_health.set_defaults(
        handler=_handle_reviewer_material_evidence_fill_guidance_health
    )

    reviewer_material_evidence_fill_guidance_status = subparsers.add_parser(
        "reviewer-material-evidence-fill-guidance-status",
        help="Summarize latest reviewer material evidence fill guidance status",
    )
    reviewer_material_evidence_fill_guidance_status.add_argument(
        "--root",
        default="outputs/reports/reviewer_material_evidence_fill_guidance",
    )
    reviewer_material_evidence_fill_guidance_status.add_argument(
        "--output-dir",
        default="outputs/reports/reviewer_material_evidence_fill_guidance/status",
    )
    reviewer_material_evidence_fill_guidance_status.set_defaults(
        handler=_handle_reviewer_material_evidence_fill_guidance_status
    )

    one_row_material_evidence_fill_package = subparsers.add_parser(
        "one-row-material-evidence-fill-package",
        help="Create a report-only one-row material evidence fill package",
    )
    one_row_material_evidence_fill_package.add_argument(
        "--audit",
        default="outputs/reports/manual_diagnostics/one_row_material_evidence_fill_package_audit_v0_1",
    )
    one_row_material_evidence_fill_package.add_argument(
        "--guidance",
        default="outputs/reports/reviewer_material_evidence_fill_guidance/94f5ff204662",
    )
    one_row_material_evidence_fill_package.add_argument(
        "--material-plan",
        default="outputs/reports/material_pit_evidence_gate_closure_plan/2d6ab8e7f9f8",
    )
    one_row_material_evidence_fill_package.add_argument(
        "--partial-impact",
        default="outputs/reports/first_batch_partial_completion_impact/ea81f81ae764",
    )
    one_row_material_evidence_fill_package.add_argument(
        "--completion-plan",
        default="outputs/reports/first_batch_reviewer_evidence_completion_plan/c630522f235a",
    )
    one_row_material_evidence_fill_package.add_argument(
        "--validator",
        default="outputs/reports/pit_evidence_checklist_validator/62e9eb747197",
    )
    one_row_material_evidence_fill_package.add_argument(
        "--enrichment",
        default="outputs/reports/pit_official_status_evidence_packet_enrichment/cb5f323d3c8c",
    )
    one_row_material_evidence_fill_package.add_argument(
        "--reviewer-no-hit-acceptance",
        default="outputs/reports/reviewer_no_hit_source_coverage_acceptance/2e05e4b74794",
    )
    one_row_material_evidence_fill_package.add_argument(
        "--reviewer-no-hit-downstream-impact",
        default="outputs/reports/reviewer_no_hit_acceptance_downstream_impact/9e164963455e",
    )
    one_row_material_evidence_fill_package.add_argument("--signal-date", default="2024-04-02")
    one_row_material_evidence_fill_package.add_argument("--symbol", default="000001")
    one_row_material_evidence_fill_package.add_argument("--universe-name", default="stock_core")
    one_row_material_evidence_fill_package.add_argument(
        "--output-dir",
        default="outputs/reports/one_row_material_evidence_fill_package",
    )
    one_row_material_evidence_fill_package.set_defaults(handler=_handle_one_row_material_evidence_fill_package)

    one_row_material_evidence_fill_package_index = subparsers.add_parser(
        "one-row-material-evidence-fill-package-index",
        help="Build a local index of one-row material evidence fill package artifacts",
    )
    one_row_material_evidence_fill_package_index.add_argument(
        "--root",
        default="outputs/reports/one_row_material_evidence_fill_package",
    )
    one_row_material_evidence_fill_package_index.add_argument(
        "--output-dir",
        default="outputs/reports/one_row_material_evidence_fill_package/index",
    )
    one_row_material_evidence_fill_package_index.set_defaults(
        handler=_handle_one_row_material_evidence_fill_package_index
    )

    one_row_material_evidence_fill_package_health = subparsers.add_parser(
        "one-row-material-evidence-fill-package-health",
        help="Check one-row material evidence fill package artifact health",
    )
    one_row_material_evidence_fill_package_health.add_argument(
        "--root",
        default="outputs/reports/one_row_material_evidence_fill_package",
    )
    one_row_material_evidence_fill_package_health.add_argument(
        "--output-dir",
        default="outputs/reports/one_row_material_evidence_fill_package/health",
    )
    one_row_material_evidence_fill_package_health.set_defaults(
        handler=_handle_one_row_material_evidence_fill_package_health
    )

    one_row_material_evidence_fill_package_status = subparsers.add_parser(
        "one-row-material-evidence-fill-package-status",
        help="Summarize latest one-row material evidence fill package status",
    )
    one_row_material_evidence_fill_package_status.add_argument(
        "--root",
        default="outputs/reports/one_row_material_evidence_fill_package",
    )
    one_row_material_evidence_fill_package_status.add_argument(
        "--output-dir",
        default="outputs/reports/one_row_material_evidence_fill_package/status",
    )
    one_row_material_evidence_fill_package_status.set_defaults(
        handler=_handle_one_row_material_evidence_fill_package_status
    )

    one_row_checklist_pass_candidate_preview = subparsers.add_parser(
        "one-row-checklist-pass-candidate-preview",
        help="Create a report-only one-row checklist-pass candidate preview",
    )
    one_row_checklist_pass_candidate_preview.add_argument(
        "--audit",
        default="outputs/reports/manual_diagnostics/one_row_checklist_pass_candidate_preview_audit_v0_1",
    )
    one_row_checklist_pass_candidate_preview.add_argument(
        "--package",
        default="outputs/reports/one_row_material_evidence_fill_package/136cbd739ca1",
    )
    one_row_checklist_pass_candidate_preview.add_argument(
        "--guidance",
        default="outputs/reports/reviewer_material_evidence_fill_guidance/94f5ff204662",
    )
    one_row_checklist_pass_candidate_preview.add_argument(
        "--material-plan",
        default="outputs/reports/material_pit_evidence_gate_closure_plan/2d6ab8e7f9f8",
    )
    one_row_checklist_pass_candidate_preview.add_argument(
        "--completion-plan",
        default="outputs/reports/first_batch_reviewer_evidence_completion_plan/c630522f235a",
    )
    one_row_checklist_pass_candidate_preview.add_argument(
        "--validator",
        default="outputs/reports/pit_evidence_checklist_validator/62e9eb747197",
    )
    one_row_checklist_pass_candidate_preview.add_argument(
        "--enrichment",
        default="outputs/reports/pit_official_status_evidence_packet_enrichment/cb5f323d3c8c",
    )
    one_row_checklist_pass_candidate_preview.add_argument(
        "--reviewer-no-hit-acceptance",
        default="outputs/reports/reviewer_no_hit_source_coverage_acceptance/2e05e4b74794",
    )
    one_row_checklist_pass_candidate_preview.add_argument(
        "--reviewer-no-hit-downstream-impact",
        default="outputs/reports/reviewer_no_hit_acceptance_downstream_impact/9e164963455e",
    )
    one_row_checklist_pass_candidate_preview.add_argument("--signal-date", default="2024-04-02")
    one_row_checklist_pass_candidate_preview.add_argument("--symbol", default="000001")
    one_row_checklist_pass_candidate_preview.add_argument("--universe-name", default="stock_core")
    one_row_checklist_pass_candidate_preview.add_argument(
        "--output-dir",
        default="outputs/reports/one_row_checklist_pass_candidate_preview",
    )
    one_row_checklist_pass_candidate_preview.set_defaults(
        handler=_handle_one_row_checklist_pass_candidate_preview
    )

    one_row_checklist_pass_candidate_preview_index = subparsers.add_parser(
        "one-row-checklist-pass-candidate-preview-index",
        help="Build a local index of one-row checklist-pass candidate preview artifacts",
    )
    one_row_checklist_pass_candidate_preview_index.add_argument(
        "--root",
        default="outputs/reports/one_row_checklist_pass_candidate_preview",
    )
    one_row_checklist_pass_candidate_preview_index.add_argument(
        "--output-dir",
        default="outputs/reports/one_row_checklist_pass_candidate_preview/index",
    )
    one_row_checklist_pass_candidate_preview_index.set_defaults(
        handler=_handle_one_row_checklist_pass_candidate_preview_index
    )

    one_row_checklist_pass_candidate_preview_health = subparsers.add_parser(
        "one-row-checklist-pass-candidate-preview-health",
        help="Check one-row checklist-pass candidate preview artifact health",
    )
    one_row_checklist_pass_candidate_preview_health.add_argument(
        "--root",
        default="outputs/reports/one_row_checklist_pass_candidate_preview",
    )
    one_row_checklist_pass_candidate_preview_health.add_argument(
        "--output-dir",
        default="outputs/reports/one_row_checklist_pass_candidate_preview/health",
    )
    one_row_checklist_pass_candidate_preview_health.set_defaults(
        handler=_handle_one_row_checklist_pass_candidate_preview_health
    )

    one_row_checklist_pass_candidate_preview_status = subparsers.add_parser(
        "one-row-checklist-pass-candidate-preview-status",
        help="Summarize latest one-row checklist-pass candidate preview status",
    )
    one_row_checklist_pass_candidate_preview_status.add_argument(
        "--root",
        default="outputs/reports/one_row_checklist_pass_candidate_preview",
    )
    one_row_checklist_pass_candidate_preview_status.add_argument(
        "--output-dir",
        default="outputs/reports/one_row_checklist_pass_candidate_preview/status",
    )
    one_row_checklist_pass_candidate_preview_status.set_defaults(
        handler=_handle_one_row_checklist_pass_candidate_preview_status
    )

    historical_replay_input_gate_validator = subparsers.add_parser(
        "historical-replay-input-gate-validator",
        help="Validate a local historical replay input package as report-only diagnostic context",
    )
    historical_replay_input_gate_validator.add_argument(
        "--input-package",
        default=None,
        help="Optional local replay input package folder containing replay_input_manifest.json and CSV components",
    )
    historical_replay_input_gate_validator.add_argument(
        "--output-dir",
        default="outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_v0_1",
        help="Directory where report-only historical replay input gate validator artifacts will be written",
    )
    historical_replay_input_gate_validator.set_defaults(handler=_handle_historical_replay_input_gate_validator)

    historical_replay_input_gate_validator_index = subparsers.add_parser(
        "historical-replay-input-gate-validator-index",
        help="Index report-only historical replay input gate validator artifacts",
    )
    historical_replay_input_gate_validator_index.add_argument(
        "--root",
        default="outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_v0_1",
        help="Validator artifact root to index",
    )
    historical_replay_input_gate_validator_index.add_argument(
        "--output-dir",
        default="outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_v0_1/index",
        help="Directory where validator index artifacts will be written",
    )
    historical_replay_input_gate_validator_index.set_defaults(
        handler=_handle_historical_replay_input_gate_validator_index
    )

    historical_replay_input_gate_validator_health = subparsers.add_parser(
        "historical-replay-input-gate-validator-health",
        help="Check report-only historical replay input gate validator artifact health",
    )
    historical_replay_input_gate_validator_health.add_argument(
        "--root",
        default="outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_v0_1",
        help="Validator artifact root to check",
    )
    historical_replay_input_gate_validator_health.add_argument(
        "--output-dir",
        default="outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_v0_1/health",
        help="Directory where validator health artifacts will be written",
    )
    historical_replay_input_gate_validator_health.set_defaults(
        handler=_handle_historical_replay_input_gate_validator_health
    )

    historical_replay_input_gate_validator_status = subparsers.add_parser(
        "historical-replay-input-gate-validator-status",
        help="Summarize latest report-only historical replay input gate validator status",
    )
    historical_replay_input_gate_validator_status.add_argument(
        "--root",
        default="outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_v0_1",
        help="Validator artifact root to summarize",
    )
    historical_replay_input_gate_validator_status.add_argument(
        "--output-dir",
        default="outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_v0_1/status",
        help="Directory where validator status artifacts will be written",
    )
    historical_replay_input_gate_validator_status.set_defaults(
        handler=_handle_historical_replay_input_gate_validator_status
    )

    historical_replay_input_gate_validator_fixture = subparsers.add_parser(
        "historical-replay-input-gate-validator-fixture",
        help="Write report-only fixture cases for a future historical replay input gate validator",
    )
    historical_replay_input_gate_validator_fixture.add_argument(
        "--output-dir",
        default="outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1",
        help="Directory where historical replay input gate validator fixture artifacts will be written",
    )
    historical_replay_input_gate_validator_fixture.set_defaults(
        handler=_handle_historical_replay_input_gate_validator_fixture
    )

    historical_replay_input_gate_validator_fixture_index = subparsers.add_parser(
        "historical-replay-input-gate-validator-fixture-index",
        help="Index report-only historical replay input gate validator fixture artifacts",
    )
    historical_replay_input_gate_validator_fixture_index.add_argument(
        "--root",
        default="outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1",
        help="Fixture artifact root to index",
    )
    historical_replay_input_gate_validator_fixture_index.add_argument(
        "--output-dir",
        default="outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1/index",
        help="Directory where fixture index artifacts will be written",
    )
    historical_replay_input_gate_validator_fixture_index.set_defaults(
        handler=_handle_historical_replay_input_gate_validator_fixture_index
    )

    historical_replay_input_gate_validator_fixture_health = subparsers.add_parser(
        "historical-replay-input-gate-validator-fixture-health",
        help="Check report-only historical replay input gate validator fixture artifact health",
    )
    historical_replay_input_gate_validator_fixture_health.add_argument(
        "--root",
        default="outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1",
        help="Fixture artifact root to check",
    )
    historical_replay_input_gate_validator_fixture_health.add_argument(
        "--output-dir",
        default="outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1/health",
        help="Directory where fixture health artifacts will be written",
    )
    historical_replay_input_gate_validator_fixture_health.set_defaults(
        handler=_handle_historical_replay_input_gate_validator_fixture_health
    )

    historical_replay_input_gate_validator_fixture_status = subparsers.add_parser(
        "historical-replay-input-gate-validator-fixture-status",
        help="Summarize latest report-only historical replay input gate validator fixture status",
    )
    historical_replay_input_gate_validator_fixture_status.add_argument(
        "--root",
        default="outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1",
        help="Fixture artifact root to summarize",
    )
    historical_replay_input_gate_validator_fixture_status.add_argument(
        "--output-dir",
        default="outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1/status",
        help="Directory where fixture status artifacts will be written",
    )
    historical_replay_input_gate_validator_fixture_status.set_defaults(
        handler=_handle_historical_replay_input_gate_validator_fixture_status
    )

    replay_substrate_schema_fixture = subparsers.add_parser(
        "replay-substrate-schema-fixture",
        help="Write report-only synthetic replay substrate schema fixture artifacts",
    )
    replay_substrate_schema_fixture.add_argument(
        "--output-dir",
        default="outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1",
        help="Directory where replay substrate schema fixture artifacts will be written",
    )
    replay_substrate_schema_fixture.set_defaults(handler=_handle_replay_substrate_schema_fixture)

    replay_substrate_schema_fixture_index = subparsers.add_parser(
        "replay-substrate-schema-fixture-index",
        help="Build an index for report-only replay substrate schema fixture artifacts",
    )
    replay_substrate_schema_fixture_index.add_argument(
        "--root",
        default="outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1",
    )
    replay_substrate_schema_fixture_index.add_argument(
        "--output-dir",
        default="outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1/index",
    )
    replay_substrate_schema_fixture_index.set_defaults(handler=_handle_replay_substrate_schema_fixture_index)

    replay_substrate_schema_fixture_health = subparsers.add_parser(
        "replay-substrate-schema-fixture-health",
        help="Check report-only replay substrate schema fixture artifact health",
    )
    replay_substrate_schema_fixture_health.add_argument(
        "--root",
        default="outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1",
    )
    replay_substrate_schema_fixture_health.add_argument(
        "--output-dir",
        default="outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1/health",
    )
    replay_substrate_schema_fixture_health.set_defaults(handler=_handle_replay_substrate_schema_fixture_health)

    replay_substrate_schema_fixture_status = subparsers.add_parser(
        "replay-substrate-schema-fixture-status",
        help="Summarize latest report-only replay substrate schema fixture status",
    )
    replay_substrate_schema_fixture_status.add_argument(
        "--root",
        default="outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1",
    )
    replay_substrate_schema_fixture_status.add_argument(
        "--output-dir",
        default="outputs/reports/manual_diagnostics/replay_substrate_schema_fixture_v0_1/status",
    )
    replay_substrate_schema_fixture_status.set_defaults(handler=_handle_replay_substrate_schema_fixture_status)

    universe_profile_policy_audit = subparsers.add_parser(
        "universe-profile-policy-audit",
        help="Audit local universe profile naming and instrument-type policy without mutating artifacts",
    )
    universe_profile_policy_audit.add_argument(
        "--worklist",
        default=None,
        help="Optional PIT universe evidence review worklist CSV",
    )
    universe_profile_policy_audit.add_argument(
        "--review",
        default=None,
        help="Optional reviewed PIT universe overlay CSV",
    )
    universe_profile_policy_audit.add_argument(
        "--output-dir",
        default="outputs/reports/universe_profile_policy_audit",
        help="Universe profile policy audit output directory",
    )
    universe_profile_policy_audit.set_defaults(handler=_handle_universe_profile_policy_audit)

    universe_profile_policy_audit_index = subparsers.add_parser(
        "universe-profile-policy-audit-index",
        help="Build a local index of universe profile policy audit artifacts",
    )
    universe_profile_policy_audit_index.add_argument(
        "--root",
        default="outputs/reports/universe_profile_policy_audit",
        help="Universe profile policy audit artifact root",
    )
    universe_profile_policy_audit_index.add_argument(
        "--output-dir",
        default="outputs/reports/universe_profile_policy_audit/index",
        help="Index output directory",
    )
    universe_profile_policy_audit_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Include folders missing metadata.json",
    )
    universe_profile_policy_audit_index.set_defaults(handler=_handle_universe_profile_policy_audit_index)

    universe_profile_policy_audit_health = subparsers.add_parser(
        "universe-profile-policy-audit-health",
        help="Check local universe profile policy audit artifact health",
    )
    universe_profile_policy_audit_health.add_argument(
        "--root",
        default="outputs/reports/universe_profile_policy_audit",
        help="Universe profile policy audit artifact root",
    )
    universe_profile_policy_audit_health.add_argument("--index", help="Optional policy audit index CSV path")
    universe_profile_policy_audit_health.add_argument(
        "--output-dir",
        default="outputs/reports/universe_profile_policy_audit/health",
        help="Health output directory",
    )
    universe_profile_policy_audit_health.set_defaults(handler=_handle_universe_profile_policy_audit_health)

    universe_profile_policy_audit_status = subparsers.add_parser(
        "universe-profile-policy-audit-status",
        help="Summarize latest local universe profile policy audit status",
    )
    universe_profile_policy_audit_status.add_argument(
        "--root",
        default="outputs/reports/universe_profile_policy_audit",
        help="Universe profile policy audit artifact root",
    )
    universe_profile_policy_audit_status.add_argument(
        "--output-dir",
        default="outputs/reports/universe_profile_policy_audit/status",
        help="Status output directory",
    )
    universe_profile_policy_audit_status.set_defaults(handler=_handle_universe_profile_policy_audit_status)

    universe_profile_split_worklist_plan = subparsers.add_parser(
        "universe-profile-split-worklist-plan",
        help="Plan future split worklists from a universe profile registry without mutating active worklists",
    )
    universe_profile_split_worklist_plan.add_argument(
        "--worklist",
        default=None,
        help="Optional PIT universe evidence review worklist CSV",
    )
    universe_profile_split_worklist_plan.add_argument(
        "--policy-audit",
        default=None,
        help="Optional universe profile policy audit CSV",
    )
    universe_profile_split_worklist_plan.add_argument(
        "--profiles",
        default="config/universe_profiles.yaml",
        help="Universe profile registry YAML",
    )
    universe_profile_split_worklist_plan.add_argument(
        "--output-dir",
        default="outputs/reports/universe_profile_split_worklist_plan",
        help="Universe profile split-worklist plan output directory",
    )
    universe_profile_split_worklist_plan.set_defaults(handler=_handle_universe_profile_split_worklist_plan)

    universe_profile_split_worklist_plan_index = subparsers.add_parser(
        "universe-profile-split-worklist-plan-index",
        help="Build a local index of universe profile split-worklist plan artifacts",
    )
    universe_profile_split_worklist_plan_index.add_argument(
        "--root",
        default="outputs/reports/universe_profile_split_worklist_plan",
        help="Universe profile split-worklist plan artifact root",
    )
    universe_profile_split_worklist_plan_index.add_argument(
        "--output-dir",
        default="outputs/reports/universe_profile_split_worklist_plan/index",
        help="Index output directory",
    )
    universe_profile_split_worklist_plan_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Include folders missing metadata.json",
    )
    universe_profile_split_worklist_plan_index.set_defaults(
        handler=_handle_universe_profile_split_worklist_plan_index
    )

    universe_profile_split_worklist_plan_health = subparsers.add_parser(
        "universe-profile-split-worklist-plan-health",
        help="Check local universe profile split-worklist plan artifact health",
    )
    universe_profile_split_worklist_plan_health.add_argument(
        "--root",
        default="outputs/reports/universe_profile_split_worklist_plan",
        help="Universe profile split-worklist plan artifact root",
    )
    universe_profile_split_worklist_plan_health.add_argument("--index", help="Optional split-worklist plan index CSV path")
    universe_profile_split_worklist_plan_health.add_argument(
        "--output-dir",
        default="outputs/reports/universe_profile_split_worklist_plan/health",
        help="Health output directory",
    )
    universe_profile_split_worklist_plan_health.set_defaults(
        handler=_handle_universe_profile_split_worklist_plan_health
    )

    universe_profile_split_worklist_plan_status = subparsers.add_parser(
        "universe-profile-split-worklist-plan-status",
        help="Summarize latest local universe profile split-worklist plan status",
    )
    universe_profile_split_worklist_plan_status.add_argument(
        "--root",
        default="outputs/reports/universe_profile_split_worklist_plan",
        help="Universe profile split-worklist plan artifact root",
    )
    universe_profile_split_worklist_plan_status.add_argument(
        "--output-dir",
        default="outputs/reports/universe_profile_split_worklist_plan/status",
        help="Status output directory",
    )
    universe_profile_split_worklist_plan_status.set_defaults(
        handler=_handle_universe_profile_split_worklist_plan_status
    )

    reviewed_replacement_worklist_plan = subparsers.add_parser(
        "reviewed-replacement-worklist-plan",
        help="Create report-only replacement worklist templates from a split-worklist plan",
    )
    reviewed_replacement_worklist_plan.add_argument(
        "--split-plan",
        default=(
            "outputs/reports/universe_profile_split_worklist_plan/"
            "db2c09268c14/universe_profile_split_worklist_plan.csv"
        ),
        help="Universe profile split-worklist plan CSV",
    )
    reviewed_replacement_worklist_plan.add_argument(
        "--output-dir",
        default="outputs/reports/reviewed_replacement_worklist_plan",
        help="Reviewed replacement worklist plan output directory",
    )
    reviewed_replacement_worklist_plan.set_defaults(handler=_handle_reviewed_replacement_worklist_plan)

    reviewed_replacement_worklist_plan_index = subparsers.add_parser(
        "reviewed-replacement-worklist-plan-index",
        help="Build a local index of reviewed replacement worklist plan artifacts",
    )
    reviewed_replacement_worklist_plan_index.add_argument(
        "--root",
        default="outputs/reports/reviewed_replacement_worklist_plan",
        help="Reviewed replacement worklist plan artifact root",
    )
    reviewed_replacement_worklist_plan_index.add_argument(
        "--output-dir",
        default="outputs/reports/reviewed_replacement_worklist_plan/index",
        help="Index output directory",
    )
    reviewed_replacement_worklist_plan_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Include folders missing metadata.json",
    )
    reviewed_replacement_worklist_plan_index.set_defaults(handler=_handle_reviewed_replacement_worklist_plan_index)

    reviewed_replacement_worklist_plan_health = subparsers.add_parser(
        "reviewed-replacement-worklist-plan-health",
        help="Check local reviewed replacement worklist plan artifact health",
    )
    reviewed_replacement_worklist_plan_health.add_argument(
        "--root",
        default="outputs/reports/reviewed_replacement_worklist_plan",
        help="Reviewed replacement worklist plan artifact root",
    )
    reviewed_replacement_worklist_plan_health.add_argument("--index", help="Optional replacement plan index CSV path")
    reviewed_replacement_worklist_plan_health.add_argument(
        "--output-dir",
        default="outputs/reports/reviewed_replacement_worklist_plan/health",
        help="Health output directory",
    )
    reviewed_replacement_worklist_plan_health.set_defaults(handler=_handle_reviewed_replacement_worklist_plan_health)

    reviewed_replacement_worklist_plan_status = subparsers.add_parser(
        "reviewed-replacement-worklist-plan-status",
        help="Summarize latest local reviewed replacement worklist plan status",
    )
    reviewed_replacement_worklist_plan_status.add_argument(
        "--root",
        default="outputs/reports/reviewed_replacement_worklist_plan",
        help="Reviewed replacement worklist plan artifact root",
    )
    reviewed_replacement_worklist_plan_status.add_argument(
        "--output-dir",
        default="outputs/reports/reviewed_replacement_worklist_plan/status",
        help="Status output directory",
    )
    reviewed_replacement_worklist_plan_status.set_defaults(handler=_handle_reviewed_replacement_worklist_plan_status)

    reviewed_replacement_worklist_acceptance = subparsers.add_parser(
        "reviewed-replacement-worklist-acceptance",
        help="Acknowledge reviewed replacement templates as report-only planning context",
    )
    reviewed_replacement_worklist_acceptance.add_argument(
        "--replacement-plan",
        default=(
            "outputs/reports/reviewed_replacement_worklist_plan/"
            "0774d0a1fdb9/reviewed_replacement_worklist_plan.csv"
        ),
        help="Reviewed replacement worklist plan CSV",
    )
    reviewed_replacement_worklist_acceptance.add_argument("--accepted-by", required=True, help="Manual acceptor name/id")
    reviewed_replacement_worklist_acceptance.add_argument("--accepted-at", required=True, help="Manual acceptance timestamp")
    reviewed_replacement_worklist_acceptance.add_argument(
        "--acceptance-reason",
        required=True,
        help="Manual acceptance reason for planning context",
    )
    reviewed_replacement_worklist_acceptance.add_argument(
        "--manual-acceptance",
        action="store_true",
        help="Required explicit acknowledgement flag",
    )
    reviewed_replacement_worklist_acceptance.add_argument(
        "--output-dir",
        default="outputs/reports/reviewed_replacement_worklist_acceptance",
        help="Reviewed replacement worklist acceptance output directory",
    )
    reviewed_replacement_worklist_acceptance.set_defaults(
        handler=_handle_reviewed_replacement_worklist_acceptance
    )

    reviewed_replacement_worklist_acceptance_index = subparsers.add_parser(
        "reviewed-replacement-worklist-acceptance-index",
        help="Build a local index of reviewed replacement worklist acceptance artifacts",
    )
    reviewed_replacement_worklist_acceptance_index.add_argument(
        "--root",
        default="outputs/reports/reviewed_replacement_worklist_acceptance",
        help="Reviewed replacement worklist acceptance artifact root",
    )
    reviewed_replacement_worklist_acceptance_index.add_argument(
        "--output-dir",
        default="outputs/reports/reviewed_replacement_worklist_acceptance/index",
        help="Index output directory",
    )
    reviewed_replacement_worklist_acceptance_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Include folders missing metadata.json",
    )
    reviewed_replacement_worklist_acceptance_index.set_defaults(
        handler=_handle_reviewed_replacement_worklist_acceptance_index
    )

    reviewed_replacement_worklist_acceptance_health = subparsers.add_parser(
        "reviewed-replacement-worklist-acceptance-health",
        help="Check local reviewed replacement worklist acceptance artifact health",
    )
    reviewed_replacement_worklist_acceptance_health.add_argument(
        "--root",
        default="outputs/reports/reviewed_replacement_worklist_acceptance",
        help="Reviewed replacement worklist acceptance artifact root",
    )
    reviewed_replacement_worklist_acceptance_health.add_argument(
        "--index",
        help="Optional replacement acceptance index CSV path",
    )
    reviewed_replacement_worklist_acceptance_health.add_argument(
        "--output-dir",
        default="outputs/reports/reviewed_replacement_worklist_acceptance/health",
        help="Health output directory",
    )
    reviewed_replacement_worklist_acceptance_health.set_defaults(
        handler=_handle_reviewed_replacement_worklist_acceptance_health
    )

    reviewed_replacement_worklist_acceptance_status = subparsers.add_parser(
        "reviewed-replacement-worklist-acceptance-status",
        help="Summarize latest local reviewed replacement worklist acceptance status",
    )
    reviewed_replacement_worklist_acceptance_status.add_argument(
        "--root",
        default="outputs/reports/reviewed_replacement_worklist_acceptance",
        help="Reviewed replacement worklist acceptance artifact root",
    )
    reviewed_replacement_worklist_acceptance_status.add_argument(
        "--output-dir",
        default="outputs/reports/reviewed_replacement_worklist_acceptance/status",
        help="Status output directory",
    )
    reviewed_replacement_worklist_acceptance_status.set_defaults(
        handler=_handle_reviewed_replacement_worklist_acceptance_status
    )

    reviewed_replacement_worklist_activation = subparsers.add_parser(
        "reviewed-replacement-worklist-activation",
        help="Activate accepted replacement templates as report-only planning context",
    )
    reviewed_replacement_worklist_activation.add_argument(
        "--acceptance",
        default=(
            "outputs/reports/reviewed_replacement_worklist_acceptance/"
            "c723c0c476b1/reviewed_replacement_worklist_acceptance.csv"
        ),
        help="Reviewed replacement worklist acceptance CSV",
    )
    reviewed_replacement_worklist_activation.add_argument("--activated-by", required=True, help="Manual activator name/id")
    reviewed_replacement_worklist_activation.add_argument("--activated-at", required=True, help="Manual activation timestamp")
    reviewed_replacement_worklist_activation.add_argument(
        "--activation-reason",
        required=True,
        help="Manual activation reason for planning context",
    )
    reviewed_replacement_worklist_activation.add_argument(
        "--manual-activation",
        action="store_true",
        help="Required explicit activation acknowledgement flag",
    )
    reviewed_replacement_worklist_activation.add_argument(
        "--output-dir",
        default="outputs/reports/reviewed_replacement_worklist_activation",
        help="Reviewed replacement worklist activation output directory",
    )
    reviewed_replacement_worklist_activation.set_defaults(
        handler=_handle_reviewed_replacement_worklist_activation
    )

    reviewed_replacement_worklist_activation_index = subparsers.add_parser(
        "reviewed-replacement-worklist-activation-index",
        help="Build a local index of reviewed replacement worklist activation artifacts",
    )
    reviewed_replacement_worklist_activation_index.add_argument(
        "--root",
        default="outputs/reports/reviewed_replacement_worklist_activation",
        help="Reviewed replacement worklist activation artifact root",
    )
    reviewed_replacement_worklist_activation_index.add_argument(
        "--output-dir",
        default="outputs/reports/reviewed_replacement_worklist_activation/index",
        help="Index output directory",
    )
    reviewed_replacement_worklist_activation_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Include folders missing metadata.json",
    )
    reviewed_replacement_worklist_activation_index.set_defaults(
        handler=_handle_reviewed_replacement_worklist_activation_index
    )

    reviewed_replacement_worklist_activation_health = subparsers.add_parser(
        "reviewed-replacement-worklist-activation-health",
        help="Check local reviewed replacement worklist activation artifact health",
    )
    reviewed_replacement_worklist_activation_health.add_argument(
        "--root",
        default="outputs/reports/reviewed_replacement_worklist_activation",
        help="Reviewed replacement worklist activation artifact root",
    )
    reviewed_replacement_worklist_activation_health.add_argument(
        "--index",
        help="Optional replacement activation index CSV path",
    )
    reviewed_replacement_worklist_activation_health.add_argument(
        "--output-dir",
        default="outputs/reports/reviewed_replacement_worklist_activation/health",
        help="Health output directory",
    )
    reviewed_replacement_worklist_activation_health.set_defaults(
        handler=_handle_reviewed_replacement_worklist_activation_health
    )

    reviewed_replacement_worklist_activation_status = subparsers.add_parser(
        "reviewed-replacement-worklist-activation-status",
        help="Summarize latest local reviewed replacement worklist activation status",
    )
    reviewed_replacement_worklist_activation_status.add_argument(
        "--root",
        default="outputs/reports/reviewed_replacement_worklist_activation",
        help="Reviewed replacement worklist activation artifact root",
    )
    reviewed_replacement_worklist_activation_status.add_argument(
        "--output-dir",
        default="outputs/reports/reviewed_replacement_worklist_activation/status",
        help="Status output directory",
    )
    reviewed_replacement_worklist_activation_status.set_defaults(
        handler=_handle_reviewed_replacement_worklist_activation_status
    )

    activated_evidence_update_plan = subparsers.add_parser(
        "activated-replacement-worklist-evidence-update-plan",
        help="Create profile-specific evidence update packages from activated replacement worklists",
    )
    activated_evidence_update_plan.add_argument(
        "--activation",
        default=(
            "outputs/reports/reviewed_replacement_worklist_activation/"
            "a8e74161f9bb/reviewed_replacement_worklist_activation.csv"
        ),
        help="Reviewed replacement worklist activation CSV",
    )
    activated_evidence_update_plan.add_argument(
        "--output-dir",
        default="outputs/reports/activated_replacement_worklist_evidence_update_plan",
        help="Evidence update plan output directory",
    )
    activated_evidence_update_plan.set_defaults(
        handler=_handle_activated_replacement_worklist_evidence_update_plan
    )

    activated_evidence_update_plan_index = subparsers.add_parser(
        "activated-replacement-worklist-evidence-update-plan-index",
        help="Build a local index of activated replacement worklist evidence update plan artifacts",
    )
    activated_evidence_update_plan_index.add_argument(
        "--root",
        default="outputs/reports/activated_replacement_worklist_evidence_update_plan",
        help="Evidence update plan artifact root",
    )
    activated_evidence_update_plan_index.add_argument(
        "--output-dir",
        default="outputs/reports/activated_replacement_worklist_evidence_update_plan/index",
        help="Index output directory",
    )
    activated_evidence_update_plan_index.set_defaults(
        handler=_handle_activated_replacement_worklist_evidence_update_plan_index
    )

    activated_evidence_update_plan_health = subparsers.add_parser(
        "activated-replacement-worklist-evidence-update-plan-health",
        help="Check activated replacement worklist evidence update plan health",
    )
    activated_evidence_update_plan_health.add_argument(
        "--root",
        default="outputs/reports/activated_replacement_worklist_evidence_update_plan",
        help="Evidence update plan artifact root",
    )
    activated_evidence_update_plan_health.add_argument(
        "--output-dir",
        default="outputs/reports/activated_replacement_worklist_evidence_update_plan/health",
        help="Health output directory",
    )
    activated_evidence_update_plan_health.set_defaults(
        handler=_handle_activated_replacement_worklist_evidence_update_plan_health
    )

    activated_evidence_update_plan_status = subparsers.add_parser(
        "activated-replacement-worklist-evidence-update-plan-status",
        help="Summarize latest activated replacement worklist evidence update plan status",
    )
    activated_evidence_update_plan_status.add_argument(
        "--root",
        default="outputs/reports/activated_replacement_worklist_evidence_update_plan",
        help="Evidence update plan artifact root",
    )
    activated_evidence_update_plan_status.add_argument(
        "--output-dir",
        default="outputs/reports/activated_replacement_worklist_evidence_update_plan/status",
        help="Status output directory",
    )
    activated_evidence_update_plan_status.set_defaults(
        handler=_handle_activated_replacement_worklist_evidence_update_plan_status
    )

    pit_universe_evidence_completion_helper_index = subparsers.add_parser(
        "pit-universe-evidence-completion-helper-index",
        help="Build a local index of PIT universe evidence completion helper artifacts",
    )
    pit_universe_evidence_completion_helper_index.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_evidence_completion_helper",
        help="PIT universe evidence completion helper artifact root",
    )
    pit_universe_evidence_completion_helper_index.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_evidence_completion_helper/index",
        help="Index output directory",
    )
    pit_universe_evidence_completion_helper_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Include folders missing metadata.json",
    )
    pit_universe_evidence_completion_helper_index.set_defaults(
        handler=_handle_pit_universe_evidence_completion_helper_index
    )

    pit_universe_evidence_completion_helper_health = subparsers.add_parser(
        "pit-universe-evidence-completion-helper-health",
        help="Check local PIT universe evidence completion helper artifact health",
    )
    pit_universe_evidence_completion_helper_health.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_evidence_completion_helper",
        help="PIT universe evidence completion helper artifact root",
    )
    pit_universe_evidence_completion_helper_health.add_argument("--index", help="Optional helper index CSV path")
    pit_universe_evidence_completion_helper_health.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_evidence_completion_helper/health",
        help="Health output directory",
    )
    pit_universe_evidence_completion_helper_health.set_defaults(
        handler=_handle_pit_universe_evidence_completion_helper_health
    )

    pit_universe_evidence_completion_helper_status = subparsers.add_parser(
        "pit-universe-evidence-completion-helper-status",
        help="Summarize latest local PIT universe evidence completion helper status",
    )
    pit_universe_evidence_completion_helper_status.add_argument(
        "--root",
        default="outputs/reports/point_in_time_universe_evidence_completion_helper",
        help="PIT universe evidence completion helper artifact root",
    )
    pit_universe_evidence_completion_helper_status.add_argument(
        "--output-dir",
        default="outputs/reports/point_in_time_universe_evidence_completion_helper/status",
        help="Status output directory",
    )
    pit_universe_evidence_completion_helper_status.set_defaults(
        handler=_handle_pit_universe_evidence_completion_helper_status
    )

    current_backfill_execution_manifest_index = subparsers.add_parser(
        "current-candidates-backfill-execution-manifest-index",
        help="Build a local index of current-candidates backfill execution manifest artifacts",
    )
    current_backfill_execution_manifest_index.add_argument(
        "--root",
        default="outputs/reports/current_candidates_backfill_execution_manifest",
        help="Execution manifest artifact root",
    )
    current_backfill_execution_manifest_index.add_argument(
        "--output-dir",
        default="outputs/reports/current_candidates_backfill_execution_manifest/index",
        help="Index output directory",
    )
    current_backfill_execution_manifest_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Include folders missing metadata.json",
    )
    current_backfill_execution_manifest_index.set_defaults(
        handler=_handle_current_candidates_backfill_execution_manifest_index
    )

    current_backfill_execution_manifest_health = subparsers.add_parser(
        "current-candidates-backfill-execution-manifest-health",
        help="Check local current-candidates backfill execution manifest artifact health",
    )
    current_backfill_execution_manifest_health.add_argument(
        "--root",
        default="outputs/reports/current_candidates_backfill_execution_manifest",
        help="Execution manifest artifact root",
    )
    current_backfill_execution_manifest_health.add_argument("--index", help="Optional execution manifest index CSV path")
    current_backfill_execution_manifest_health.add_argument(
        "--output-dir",
        default="outputs/reports/current_candidates_backfill_execution_manifest/health",
        help="Health output directory",
    )
    current_backfill_execution_manifest_health.set_defaults(
        handler=_handle_current_candidates_backfill_execution_manifest_health
    )

    current_backfill_execution_manifest_status = subparsers.add_parser(
        "current-candidates-backfill-execution-manifest-status",
        help="Summarize latest local current-candidates backfill execution manifest status",
    )
    current_backfill_execution_manifest_status.add_argument(
        "--root",
        default="outputs/reports/current_candidates_backfill_execution_manifest",
        help="Execution manifest artifact root",
    )
    current_backfill_execution_manifest_status.add_argument(
        "--output-dir",
        default="outputs/reports/current_candidates_backfill_execution_manifest/status",
        help="Status output directory",
    )
    current_backfill_execution_manifest_status.set_defaults(
        handler=_handle_current_candidates_backfill_execution_manifest_status
    )

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

    signal_advisory = subparsers.add_parser(
        "signal-advisory",
        help="Build local advisory signals and alert previews from current-candidates artifacts",
    )
    signal_advisory.add_argument("--candidates", required=True, help="Current-candidates candidates.csv path")
    signal_advisory.add_argument("--candidate-report", help="Optional current_candidates_report.md path")
    signal_advisory.add_argument("--metadata", help="Optional current-candidates metadata.json path")
    signal_advisory.add_argument("--output-dir", help="Optional signal advisory output directory")
    signal_advisory.add_argument(
        "--alert-preview",
        action="store_true",
        help="Print local alert preview artifact path. No message is sent.",
    )
    signal_advisory.add_argument("--config", help="Optional config YAML path")
    signal_advisory.set_defaults(handler=_handle_signal_advisory)

    signal_semantics = subparsers.add_parser(
        "signal-semantics",
        help="Map local candidate/scored rows to safe advisory semantics labels",
    )
    signal_semantics.add_argument("--input", required=True, help="Input candidates/scored/signals CSV path")
    signal_semantics.add_argument(
        "--input-type",
        required=True,
        choices=["candidates", "scored", "scored_dataset", "signals", "factor_dataset"],
        help="Input artifact type",
    )
    signal_semantics.add_argument("--metadata", help="Optional source metadata.json path")
    signal_semantics.add_argument("--snapshot-quality-status", choices=["PASS", "WARN", "FAIL"], help="Override snapshot quality status")
    signal_semantics.add_argument("--data-quality-status", choices=["PASS", "WARN", "FAIL"], help="Override data quality status")
    signal_semantics.add_argument("--profile", help="Override selection/advisory profile, such as demo or reviewed_local_v0")
    signal_semantics.add_argument("--output-dir", help="Optional signal semantics output directory")
    signal_semantics.add_argument("--config", help="Optional config YAML path")
    signal_semantics.set_defaults(handler=_handle_signal_semantics)

    advisory_profile_calibration = subparsers.add_parser(
        "advisory-profile-calibration",
        help="Analyze local advisory profile thresholds without creating orders or recommendations",
    )
    advisory_profile_calibration.add_argument("--input", required=True, help="Input candidates/scored CSV path")
    advisory_profile_calibration.add_argument(
        "--input-type",
        required=True,
        choices=["candidates", "scored_dataset"],
        help="Input artifact type",
    )
    advisory_profile_calibration.add_argument(
        "--profile",
        required=True,
        choices=["conservative", "balanced", "experimental"],
        help="Calibration profile to evaluate",
    )
    advisory_profile_calibration.add_argument(
        "--snapshot-quality-status",
        choices=["PASS", "WARN", "FAIL"],
        help="Override snapshot quality status",
    )
    advisory_profile_calibration.add_argument(
        "--data-quality-status",
        choices=["PASS", "WARN", "FAIL"],
        help="Override data quality status",
    )
    advisory_profile_calibration.add_argument("--output-dir", help="Optional calibration output directory")
    advisory_profile_calibration.add_argument("--config", help="Optional config YAML path")
    advisory_profile_calibration.set_defaults(handler=_handle_advisory_profile_calibration)

    advisory_profile_calibration_index = subparsers.add_parser(
        "advisory-profile-calibration-index",
        help="Build a local index of advisory profile calibration artifact folders",
    )
    advisory_profile_calibration_index.add_argument("--root", help="Advisory profile calibration artifact root directory")
    advisory_profile_calibration_index.add_argument("--output-dir", help="Optional calibration index output directory")
    advisory_profile_calibration_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Index folders missing metadata.json",
    )
    advisory_profile_calibration_index.add_argument("--config", help="Optional config YAML path")
    advisory_profile_calibration_index.set_defaults(handler=_handle_advisory_profile_calibration_index)

    advisory_profile_calibration_health = subparsers.add_parser(
        "advisory-profile-calibration-health",
        help="Check local advisory profile calibration artifact file health and safety flags",
    )
    advisory_profile_calibration_health.add_argument("--index", help="Advisory profile calibration artifact index CSV path")
    advisory_profile_calibration_health.add_argument("--root", help="Advisory profile calibration artifact root directory")
    advisory_profile_calibration_health.add_argument("--output-dir", help="Optional calibration health-check output directory")
    advisory_profile_calibration_health.add_argument("--strict", action="store_true", help="Escalate configurable warnings to errors")
    advisory_profile_calibration_health.add_argument("--allow-warn", action="store_true", help="Exit zero when status is WARN in strict mode")
    advisory_profile_calibration_health.add_argument("--config", help="Optional config YAML path")
    advisory_profile_calibration_health.set_defaults(handler=_handle_advisory_profile_calibration_health)

    advisory_profile_calibration_status = subparsers.add_parser(
        "advisory-profile-calibration-status",
        help="Build a local advisory profile calibration status dashboard",
    )
    advisory_profile_calibration_status.add_argument("--root", help="Advisory profile calibration artifact root directory")
    advisory_profile_calibration_status.add_argument("--output-dir", help="Optional calibration status output directory")
    advisory_profile_calibration_status.add_argument("--strict", action="store_true", help="Exit non-zero when status is WARN")
    advisory_profile_calibration_status.add_argument("--config", help="Optional config YAML path")
    advisory_profile_calibration_status.set_defaults(handler=_handle_advisory_profile_calibration_status)

    calibration_to_signal_semantics = subparsers.add_parser(
        "calibration-to-signal-semantics",
        help="Build a read-only profile proposal from calibration artifacts to signal semantics defaults",
    )
    calibration_to_signal_semantics.add_argument(
        "--calibration-root",
        default="outputs/reports/advisory_profile_calibration",
        help="Advisory profile calibration artifact root directory",
    )
    calibration_to_signal_semantics.add_argument(
        "--semantics-config",
        default="config/default.yaml",
        help="Config YAML containing current signal_semantics defaults",
    )
    calibration_to_signal_semantics.add_argument(
        "--output-dir",
        default="outputs/reports/calibration_to_signal_semantics",
        help="Optional calibration-to-semantics proposal output directory",
    )
    calibration_to_signal_semantics.set_defaults(handler=_handle_calibration_to_signal_semantics)

    calibration_to_signal_semantics_index = subparsers.add_parser(
        "calibration-to-signal-semantics-index",
        help="Build a local index of calibration-to-signal-semantics proposal artifacts",
    )
    calibration_to_signal_semantics_index.add_argument(
        "--root",
        help="Calibration-to-signal-semantics proposal artifact root directory",
    )
    calibration_to_signal_semantics_index.add_argument("--output-dir", help="Optional proposal index output directory")
    calibration_to_signal_semantics_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Index folders missing metadata.json",
    )
    calibration_to_signal_semantics_index.set_defaults(handler=_handle_calibration_to_signal_semantics_index)

    calibration_to_signal_semantics_health = subparsers.add_parser(
        "calibration-to-signal-semantics-health",
        help="Check local calibration-to-signal-semantics proposal artifact safety",
    )
    calibration_to_signal_semantics_health.add_argument("--index", help="Proposal artifact index CSV path")
    calibration_to_signal_semantics_health.add_argument("--root", help="Proposal artifact root directory")
    calibration_to_signal_semantics_health.add_argument("--output-dir", help="Optional proposal health-check output directory")
    calibration_to_signal_semantics_health.add_argument("--strict", action="store_true", help="Escalate configurable warnings to errors")
    calibration_to_signal_semantics_health.add_argument("--allow-warn", action="store_true", help="Exit zero when status is WARN in strict mode")
    calibration_to_signal_semantics_health.set_defaults(handler=_handle_calibration_to_signal_semantics_health)

    calibration_to_signal_semantics_status = subparsers.add_parser(
        "calibration-to-signal-semantics-status",
        help="Build a local calibration-to-signal-semantics proposal status dashboard",
    )
    calibration_to_signal_semantics_status.add_argument("--root", help="Proposal artifact root directory")
    calibration_to_signal_semantics_status.add_argument("--output-dir", help="Optional proposal status output directory")
    calibration_to_signal_semantics_status.add_argument("--strict", action="store_true", help="Exit non-zero when status is WARN")
    calibration_to_signal_semantics_status.set_defaults(handler=_handle_calibration_to_signal_semantics_status)

    signal_semantics_index = subparsers.add_parser(
        "signal-semantics-index",
        help="Build a local index of signal semantics artifact folders",
    )
    signal_semantics_index.add_argument("--root", help="Signal semantics artifact root directory")
    signal_semantics_index.add_argument("--output-dir", help="Optional semantics index output directory")
    signal_semantics_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Index folders missing metadata.json",
    )
    signal_semantics_index.add_argument("--config", help="Optional config YAML path")
    signal_semantics_index.set_defaults(handler=_handle_signal_semantics_index)

    signal_semantics_health = subparsers.add_parser(
        "signal-semantics-health",
        help="Check local signal semantics artifact file health and safety flags",
    )
    signal_semantics_health.add_argument("--index", help="Signal semantics artifact index CSV path")
    signal_semantics_health.add_argument("--root", help="Signal semantics artifact root directory")
    signal_semantics_health.add_argument("--output-dir", help="Optional semantics health-check output directory")
    signal_semantics_health.add_argument("--strict", action="store_true", help="Escalate configurable warnings to errors")
    signal_semantics_health.add_argument("--allow-warn", action="store_true", help="Exit zero when status is WARN in strict mode")
    signal_semantics_health.add_argument("--config", help="Optional config YAML path")
    signal_semantics_health.set_defaults(handler=_handle_signal_semantics_health)

    signal_semantics_status = subparsers.add_parser(
        "signal-semantics-status",
        help="Build a local signal semantics status dashboard",
    )
    signal_semantics_status.add_argument("--root", help="Signal semantics artifact root directory")
    signal_semantics_status.add_argument("--output-dir", help="Optional semantics status output directory")
    signal_semantics_status.add_argument("--strict", action="store_true", help="Exit non-zero when status is WARN")
    signal_semantics_status.add_argument("--config", help="Optional config YAML path")
    signal_semantics_status.set_defaults(handler=_handle_signal_semantics_status)

    signal_advisory_index = subparsers.add_parser(
        "signal-advisory-index",
        help="Build a local index of signal advisory artifact folders",
    )
    signal_advisory_index.add_argument("--root", help="Signal advisory artifact root directory")
    signal_advisory_index.add_argument("--output-dir", help="Optional index output directory")
    signal_advisory_index.add_argument("--include-missing-metadata", action="store_true", help="Index folders missing metadata.json")
    signal_advisory_index.add_argument("--config", help="Optional config YAML path")
    signal_advisory_index.set_defaults(handler=_handle_signal_advisory_index)

    signal_advisory_health = subparsers.add_parser(
        "signal-advisory-health",
        help="Check local signal advisory artifact file health and safety flags",
    )
    signal_advisory_health.add_argument("--index", help="Signal advisory artifact index CSV path")
    signal_advisory_health.add_argument("--root", help="Signal advisory artifact root directory")
    signal_advisory_health.add_argument("--output-dir", help="Optional health-check output directory")
    signal_advisory_health.add_argument("--strict", action="store_true", help="Escalate configurable warnings to errors")
    signal_advisory_health.add_argument("--allow-warn", action="store_true", help="Exit zero when status is WARN in strict mode")
    signal_advisory_health.add_argument("--config", help="Optional config YAML path")
    signal_advisory_health.set_defaults(handler=_handle_signal_advisory_health)

    signal_advisory_status = subparsers.add_parser(
        "signal-advisory-status",
        help="Build a local signal advisory status dashboard",
    )
    signal_advisory_status.add_argument("--root", help="Signal advisory artifact root directory")
    signal_advisory_status.add_argument("--output-dir", help="Optional status output directory")
    signal_advisory_status.add_argument("--strict", action="store_true", help="Exit non-zero when status is WARN")
    signal_advisory_status.add_argument("--config", help="Optional config YAML path")
    signal_advisory_status.set_defaults(handler=_handle_signal_advisory_status)

    single_symbol_advisory = subparsers.add_parser(
        "single-symbol-advisory",
        help="Build a local advisory review for one symbol from existing artifacts",
    )
    single_symbol_advisory.add_argument("--symbol", required=True, help="Symbol to review; preserved as text")
    single_symbol_advisory.add_argument("--candidates", help="Optional current-candidates candidates.csv path")
    single_symbol_advisory.add_argument("--scored-dataset", help="Optional scored_dataset.csv path")
    single_symbol_advisory.add_argument("--factor-dataset", help="Optional factor_dataset.csv path")
    single_symbol_advisory.add_argument("--signals", help="Optional signal advisory signals.csv path")
    single_symbol_advisory.add_argument("--metadata", help="Optional source metadata.json path")
    single_symbol_advisory.add_argument("--snapshot-manifest", help="Optional snapshot manifest path")
    single_symbol_advisory.add_argument("--date", help="Optional advisory date")
    single_symbol_advisory.add_argument("--output-dir", help="Optional single-symbol advisory output directory")
    single_symbol_advisory.add_argument("--answer-output-dir", help="Optional question-style answer output directory")
    single_symbol_advisory.add_argument("--question", help="Optional user question to echo in question-style output")
    single_symbol_advisory.add_argument(
        "--answer-style",
        choices=["concise", "detailed"],
        default="concise",
        help="Question-style answer rendering depth",
    )
    single_symbol_advisory.add_argument(
        "--question-style",
        action="store_true",
        help="Write a deterministic local question-style answer. No LLM or message delivery is used.",
    )
    single_symbol_advisory.add_argument(
        "--alert-preview",
        action="store_true",
        help="Write a local alert preview markdown file. No message is sent.",
    )
    single_symbol_advisory.add_argument("--config", help="Optional config YAML path")
    single_symbol_advisory.set_defaults(handler=_handle_single_symbol_advisory)

    single_symbol_advisory_index = subparsers.add_parser(
        "single-symbol-advisory-index",
        help="Build a local index of single-symbol advisory artifact folders",
    )
    single_symbol_advisory_index.add_argument("--root", help="Single-symbol advisory artifact root directory")
    single_symbol_advisory_index.add_argument("--output-dir", help="Optional index output directory")
    single_symbol_advisory_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Index folders missing metadata.json",
    )
    single_symbol_advisory_index.add_argument("--config", help="Optional config YAML path")
    single_symbol_advisory_index.set_defaults(handler=_handle_single_symbol_advisory_index)

    single_symbol_advisory_health = subparsers.add_parser(
        "single-symbol-advisory-health",
        help="Check local single-symbol advisory artifact file health and safety flags",
    )
    single_symbol_advisory_health.add_argument("--index", help="Single-symbol advisory artifact index CSV path")
    single_symbol_advisory_health.add_argument("--root", help="Single-symbol advisory artifact root directory")
    single_symbol_advisory_health.add_argument("--output-dir", help="Optional health-check output directory")
    single_symbol_advisory_health.add_argument("--strict", action="store_true", help="Escalate configurable warnings to errors")
    single_symbol_advisory_health.add_argument("--allow-warn", action="store_true", help="Exit zero when status is WARN in strict mode")
    single_symbol_advisory_health.add_argument("--config", help="Optional config YAML path")
    single_symbol_advisory_health.set_defaults(handler=_handle_single_symbol_advisory_health)

    single_symbol_advisory_status = subparsers.add_parser(
        "single-symbol-advisory-status",
        help="Build a local single-symbol advisory status dashboard",
    )
    single_symbol_advisory_status.add_argument("--root", help="Single-symbol advisory artifact root directory")
    single_symbol_advisory_status.add_argument("--output-dir", help="Optional status output directory")
    single_symbol_advisory_status.add_argument("--strict", action="store_true", help="Exit non-zero when status is WARN")
    single_symbol_advisory_status.add_argument("--config", help="Optional config YAML path")
    single_symbol_advisory_status.set_defaults(handler=_handle_single_symbol_advisory_status)

    single_symbol_advisory_answer_index = subparsers.add_parser(
        "single-symbol-advisory-answer-index",
        help="Build a local index of question-style single-symbol advisory answer folders",
    )
    single_symbol_advisory_answer_index.add_argument("--root", help="Single-symbol advisory answer artifact root directory")
    single_symbol_advisory_answer_index.add_argument("--output-dir", help="Optional answer index output directory")
    single_symbol_advisory_answer_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Index answer folders missing metadata.json",
    )
    single_symbol_advisory_answer_index.add_argument("--config", help="Optional config YAML path")
    single_symbol_advisory_answer_index.set_defaults(handler=_handle_single_symbol_advisory_answer_index)

    single_symbol_advisory_answer_health = subparsers.add_parser(
        "single-symbol-advisory-answer-health",
        help="Check local question-style answer artifact file health and safety flags",
    )
    single_symbol_advisory_answer_health.add_argument("--index", help="Single-symbol advisory answer artifact index CSV path")
    single_symbol_advisory_answer_health.add_argument("--root", help="Single-symbol advisory answer artifact root directory")
    single_symbol_advisory_answer_health.add_argument("--output-dir", help="Optional answer health-check output directory")
    single_symbol_advisory_answer_health.add_argument("--strict", action="store_true", help="Escalate configurable warnings to errors")
    single_symbol_advisory_answer_health.add_argument("--allow-warn", action="store_true", help="Exit zero when status is WARN in strict mode")
    single_symbol_advisory_answer_health.add_argument("--config", help="Optional config YAML path")
    single_symbol_advisory_answer_health.set_defaults(handler=_handle_single_symbol_advisory_answer_health)

    single_symbol_advisory_answer_status = subparsers.add_parser(
        "single-symbol-advisory-answer-status",
        help="Build a local question-style answer status dashboard",
    )
    single_symbol_advisory_answer_status.add_argument("--root", help="Single-symbol advisory answer artifact root directory")
    single_symbol_advisory_answer_status.add_argument("--output-dir", help="Optional answer status output directory")
    single_symbol_advisory_answer_status.add_argument("--strict", action="store_true", help="Exit non-zero when status is WARN")
    single_symbol_advisory_answer_status.add_argument("--config", help="Optional config YAML path")
    single_symbol_advisory_answer_status.set_defaults(handler=_handle_single_symbol_advisory_answer_status)

    advisory_conversation = subparsers.add_parser(
        "advisory-conversation",
        help="Parse a local advisory question and route it to deterministic single-symbol advisory answer artifacts",
    )
    advisory_conversation.add_argument("--question", required=True, help="User question to parse locally")
    advisory_conversation.add_argument("--candidates", help="Optional current-candidates candidates.csv path")
    advisory_conversation.add_argument("--scored-dataset", help="Optional scored_dataset.csv path")
    advisory_conversation.add_argument("--factor-dataset", help="Optional factor_dataset.csv path")
    advisory_conversation.add_argument("--signals", help="Optional signal advisory signals.csv path")
    advisory_conversation.add_argument("--metadata", help="Optional source metadata.json path")
    advisory_conversation.add_argument("--snapshot-manifest", help="Optional snapshot manifest path")
    advisory_conversation.add_argument(
        "--answer-style",
        choices=["concise", "detailed"],
        default=None,
        help="Question-style answer rendering depth",
    )
    advisory_conversation.add_argument("--output-dir", help="Optional advisory conversation output directory")
    advisory_conversation.add_argument("--config", help="Optional config YAML path")
    advisory_conversation.set_defaults(handler=_handle_advisory_conversation)

    advisory_conversation_index = subparsers.add_parser(
        "advisory-conversation-index",
        help="Build a local index of advisory conversation artifact folders",
    )
    advisory_conversation_index.add_argument("--root", help="Advisory conversation artifact root directory")
    advisory_conversation_index.add_argument("--output-dir", help="Optional conversation index output directory")
    advisory_conversation_index.add_argument(
        "--include-missing-metadata",
        action="store_true",
        help="Index folders missing metadata.json",
    )
    advisory_conversation_index.add_argument("--config", help="Optional config YAML path")
    advisory_conversation_index.set_defaults(handler=_handle_advisory_conversation_index)

    advisory_conversation_health = subparsers.add_parser(
        "advisory-conversation-health",
        help="Check local advisory conversation artifact file health and safety flags",
    )
    advisory_conversation_health.add_argument("--index", help="Advisory conversation artifact index CSV path")
    advisory_conversation_health.add_argument("--root", help="Advisory conversation artifact root directory")
    advisory_conversation_health.add_argument("--output-dir", help="Optional conversation health-check output directory")
    advisory_conversation_health.add_argument("--strict", action="store_true", help="Escalate configurable warnings to errors")
    advisory_conversation_health.add_argument("--allow-warn", action="store_true", help="Exit zero when status is WARN in strict mode")
    advisory_conversation_health.add_argument("--config", help="Optional config YAML path")
    advisory_conversation_health.set_defaults(handler=_handle_advisory_conversation_health)

    advisory_conversation_status = subparsers.add_parser(
        "advisory-conversation-status",
        help="Build a local advisory conversation status dashboard",
    )
    advisory_conversation_status.add_argument("--root", help="Advisory conversation artifact root directory")
    advisory_conversation_status.add_argument("--output-dir", help="Optional conversation status output directory")
    advisory_conversation_status.add_argument("--strict", action="store_true", help="Exit non-zero when status is WARN")
    advisory_conversation_status.add_argument("--config", help="Optional config YAML path")
    advisory_conversation_status.set_defaults(handler=_handle_advisory_conversation_status)

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
    reconcile.add_argument(
        "--artifact-scope",
        choices=["active", "diagnostic"],
        default="active",
        help="Whether the reconciliation artifact belongs to the active workflow or diagnostic audit context",
    )
    reconcile.add_argument("--diagnostic-reason", help="Optional reason for diagnostic reconciliation artifacts")
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
    research_status.add_argument("--historical-backfill-root", help="Historical-backfill artifact root directory")
    research_status.add_argument(
        "--market-cache-export-policy-root",
        help="Market-cache-export policy recommendation artifact root directory",
    )
    research_status.add_argument("--market-cache-export-root", help="Market-cache-export artifact root directory")
    research_status.add_argument("--data-preparation-root", help="Data preparation artifact root directory")
    research_status.add_argument("--current-candidates-root", help="Current-candidates artifact root directory")
    research_status.add_argument(
        "--current-candidates-backfill-plan-root",
        help="Current-candidates backfill plan artifact root directory",
    )
    research_status.add_argument(
        "--current-candidates-backfill-execution-manifest-root",
        help="Current-candidates backfill execution manifest artifact root directory",
    )
    research_status.add_argument(
        "--pit-universe-overlay-plan-root",
        help="Point-in-time universe overlay plan artifact root directory",
    )
    research_status.add_argument(
        "--pit-universe-overlay-review-root",
        help="Reviewed point-in-time universe overlay artifact root directory",
    )
    research_status.add_argument(
        "--pit-universe-overlay-export-readiness-root",
        help="PIT universe overlay export-readiness artifact root directory",
    )
    research_status.add_argument(
        "--pit-universe-export-staging-root",
        help="PIT universe export staging artifact root directory",
    )
    research_status.add_argument(
        "--pit-universe-evidence-completion-helper-root",
        help="PIT universe evidence completion helper artifact root directory",
    )
    research_status.add_argument(
        "--pit-universe-evidence-review-worklist-root",
        help="PIT universe evidence review worklist artifact root directory",
    )
    research_status.add_argument(
        "--pit-universe-evidence-update-ingestion-root",
        help="PIT universe evidence update ingestion artifact root directory",
    )
    research_status.add_argument(
        "--pit-evidence-checklist-validator-root",
        help="PIT evidence checklist validator artifact root directory",
    )
    research_status.add_argument(
        "--pit-evidence-policy-profile-comparison-root",
        help="PIT evidence policy profile comparison artifact root directory",
    )
    research_status.add_argument(
        "--pit-official-status-evidence-packet-root",
        help="PIT official status evidence packet artifact root directory",
    )
    research_status.add_argument(
        "--pit-official-status-evidence-packet-enrichment-root",
        help="PIT official status evidence packet enrichment artifact root directory",
    )
    research_status.add_argument(
        "--reviewer-no-hit-source-coverage-acceptance-root",
        help="Reviewer no-hit source coverage acceptance artifact root directory",
    )
    research_status.add_argument(
        "--reviewer-no-hit-acceptance-downstream-impact-root",
        help="Reviewer no-hit acceptance downstream impact artifact root directory",
    )
    research_status.add_argument(
        "--first-batch-reviewer-evidence-completion-plan-root",
        help="First-batch reviewer evidence completion plan artifact root directory",
    )
    research_status.add_argument(
        "--first-batch-partial-completion-impact-root",
        help="First-batch partial completion impact artifact root directory",
    )
    research_status.add_argument(
        "--material-pit-evidence-gate-closure-plan-root",
        help="Material PIT evidence gate closure plan artifact root directory",
    )
    research_status.add_argument(
        "--one-row-material-evidence-fill-package-root",
        help="One-row material evidence fill package artifact root directory",
    )
    research_status.add_argument(
        "--universe-profile-policy-audit-root",
        help="Universe profile policy audit artifact root directory",
    )
    research_status.add_argument(
        "--universe-profile-split-worklist-plan-root",
        help="Universe profile split-worklist plan artifact root directory",
    )
    research_status.add_argument(
        "--reviewed-replacement-worklist-plan-root",
        help="Reviewed replacement worklist plan artifact root directory",
    )
    research_status.add_argument(
        "--reviewed-replacement-worklist-acceptance-root",
        help="Reviewed replacement worklist acceptance artifact root directory",
    )
    research_status.add_argument(
        "--reviewed-replacement-worklist-activation-root",
        help="Reviewed replacement worklist activation artifact root directory",
    )
    research_status.add_argument(
        "--activated-replacement-worklist-evidence-update-plan-root",
        help="Activated replacement worklist evidence update plan artifact root directory",
    )
    research_status.add_argument(
        "--advisory-profile-calibration-root",
        help="Advisory profile calibration artifact root directory",
    )
    research_status.add_argument(
        "--calibration-to-signal-semantics-root",
        help="Calibration-to-signal-semantics proposal artifact root directory",
    )
    research_status.add_argument("--signal-semantics-root", help="Signal semantics artifact root directory")
    research_status.add_argument("--single-symbol-advisory-root", help="Single-symbol advisory artifact root directory")
    research_status.add_argument(
        "--single-symbol-advisory-answer-root",
        help="Question-style single-symbol advisory answer artifact root directory",
    )
    research_status.add_argument(
        "--advisory-conversation-root",
        help="Local advisory conversation artifact root directory",
    )
    research_status.add_argument("--market-update-handoff-root", help="Market-update-handoff artifact root directory")
    research_status.add_argument("--paper-trading-root", help="Paper trading artifact root directory")
    research_status.add_argument("--decision-date", help="Optional decision date filter")
    research_status.add_argument("--universe", help="Optional universe name filter")
    research_status.add_argument("--output-dir", help="Optional unified dashboard output directory")
    research_status.add_argument("--strict", action="store_true", help="Exit non-zero when dashboard status is WARN")
    research_status.add_argument("--config", help="Optional config YAML path")
    research_status.set_defaults(handler=_handle_research_status)

    data_source = subparsers.add_parser("data-source-fetch", help="Fetch or load raw local market data source files")
    data_source.add_argument("--source", required=True, help="Data source adapter, e.g. LOCAL_CSV, MOCK, AKSHARE_OPTIONAL, TUSHARE_OPTIONAL, BAOSTOCK_OPTIONAL")
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
        help="Data source adapter, e.g. LOCAL_CSV, MOCK, AKSHARE_OPTIONAL, BAOSTOCK_OPTIONAL",
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
    market_cache_query.add_argument("--source", help="Optional exact source filter, e.g. AKSHARE_OPTIONAL")
    market_cache_query.add_argument("--upstream-source", help="Optional exact upstream source filter, e.g. TENCENT")
    market_cache_query.add_argument("--cache-path", help="Optional market cache CSV path")
    market_cache_query.add_argument("--output", help="Optional output CSV path for query rows")
    market_cache_query.add_argument("--config", help="Optional config YAML path")
    market_cache_query.set_defaults(handler=_handle_market_cache_query)

    market_cache_export = subparsers.add_parser(
        "market-cache-export",
        help="Export reviewed source/upstream cache selections into a pipeline-ready market CSV",
    )
    market_cache_export.add_argument("--manifest", required=True, help="Reviewed cache export CSV manifest")
    market_cache_export.add_argument("--cache-path", help="Optional market cache CSV path")
    market_cache_export.add_argument("--output-dir", help="Optional export report output directory")
    market_cache_export.add_argument("--export-output-dir", help="Optional exported market CSV output root")
    market_cache_export.add_argument("--manifest-output-dir", help="Optional generated pipeline manifest output root")
    market_cache_export.add_argument("--build-pipeline-manifest", action="store_true", help="Write a LOCAL_CSV data-pipeline manifest")
    market_cache_export.add_argument("--universe", help="Universe raw_data.csv path for generated pipeline manifest")
    market_cache_export.add_argument("--trading-calendar", help="Trading calendar raw_data.csv path for generated pipeline manifest")
    market_cache_export.add_argument("--fail-fast", action="store_true", help="Stop after the first failed manifest row")
    market_cache_export.add_argument("--config", help="Optional config YAML path")
    market_cache_export.set_defaults(handler=_handle_market_cache_export)

    market_cache_export_plan = subparsers.add_parser(
        "market-cache-export-plan",
        help="Plan a reviewed cache export using local cache coverage and source field policy",
    )
    market_cache_export_plan.add_argument("--manifest", required=True, help="Policy export request CSV manifest")
    market_cache_export_plan.add_argument("--cache-path", help="Optional market cache CSV path")
    market_cache_export_plan.add_argument("--output-dir", help="Optional policy plan report output directory")
    market_cache_export_plan.add_argument("--manifest-output-dir", help="Optional recommended manifest output root")
    market_cache_export_plan.add_argument(
        "--strict-reliable",
        action="store_true",
        help="Require every requested field to be RELIABLE; reject PROVISIONAL/UNKNOWN/caveat fields",
    )
    market_cache_export_plan.add_argument("--fail-fast", action="store_true", help="Stop after the first failed request row")
    market_cache_export_plan.add_argument("--config", help="Optional config YAML path")
    market_cache_export_plan.set_defaults(handler=_handle_market_cache_export_plan)

    market_cache_export_plan_index = subparsers.add_parser(
        "market-cache-export-plan-index",
        help="Build a local index of market-cache-export policy recommendation plans",
    )
    market_cache_export_plan_index.add_argument("--root", help="Market-cache-export policy artifact root directory")
    market_cache_export_plan_index.add_argument("--output-dir", help="Optional index output directory")
    market_cache_export_plan_index.add_argument("--include-missing-metadata", action="store_true", help="Index folders missing metadata.json")
    market_cache_export_plan_index.add_argument("--config", help="Optional config YAML path")
    market_cache_export_plan_index.set_defaults(handler=_handle_market_cache_export_plan_index)

    market_cache_export_plan_health = subparsers.add_parser(
        "market-cache-export-plan-health",
        help="Check local market-cache-export policy recommendation artifact health",
    )
    market_cache_export_plan_health.add_argument("--index", help="Market-cache-export policy index CSV path")
    market_cache_export_plan_health.add_argument("--root", help="Market-cache-export policy artifact root directory")
    market_cache_export_plan_health.add_argument("--output-dir", help="Optional health-check output directory")
    market_cache_export_plan_health.add_argument("--strict", action="store_true", help="Escalate WARN health status to non-zero exit")
    market_cache_export_plan_health.add_argument("--allow-warn", action="store_true", help="Exit zero when status is WARN in strict mode")
    market_cache_export_plan_health.add_argument("--config", help="Optional config YAML path")
    market_cache_export_plan_health.set_defaults(handler=_handle_market_cache_export_plan_health)

    market_cache_export_plan_status = subparsers.add_parser(
        "market-cache-export-plan-status",
        help="Summarize the latest market-cache-export policy recommendation plan status",
    )
    market_cache_export_plan_status.add_argument("--root", help="Market-cache-export policy artifact root directory")
    market_cache_export_plan_status.add_argument("--output-dir", help="Optional status output directory")
    market_cache_export_plan_status.add_argument("--strict", action="store_true", help="Exit non-zero when status is WARN")
    market_cache_export_plan_status.add_argument("--config", help="Optional config YAML path")
    market_cache_export_plan_status.set_defaults(handler=_handle_market_cache_export_plan_status)

    market_cache_export_index = subparsers.add_parser(
        "market-cache-export-index",
        help="Build a local index of reviewed market-cache-export artifacts",
    )
    market_cache_export_index.add_argument("--root", help="Market-cache-export artifact root directory")
    market_cache_export_index.add_argument("--output-dir", help="Optional index output directory")
    market_cache_export_index.add_argument("--include-missing-metadata", action="store_true", help="Index folders missing metadata.json")
    market_cache_export_index.add_argument("--config", help="Optional config YAML path")
    market_cache_export_index.set_defaults(handler=_handle_market_cache_export_index)

    market_cache_export_health = subparsers.add_parser(
        "market-cache-export-health",
        help="Check local reviewed market-cache-export artifact health",
    )
    market_cache_export_health.add_argument("--index", help="Market-cache-export index CSV path")
    market_cache_export_health.add_argument("--root", help="Market-cache-export artifact root directory")
    market_cache_export_health.add_argument("--output-dir", help="Optional health-check output directory")
    market_cache_export_health.add_argument("--strict", action="store_true", help="Escalate WARN health status to non-zero exit")
    market_cache_export_health.add_argument("--allow-warn", action="store_true", help="Exit zero when status is WARN in strict mode")
    market_cache_export_health.add_argument("--config", help="Optional config YAML path")
    market_cache_export_health.set_defaults(handler=_handle_market_cache_export_health)

    market_cache_export_status = subparsers.add_parser(
        "market-cache-export-status",
        help="Summarize the latest reviewed market-cache-export artifact status",
    )
    market_cache_export_status.add_argument("--root", help="Market-cache-export artifact root directory")
    market_cache_export_status.add_argument("--output-dir", help="Optional status output directory")
    market_cache_export_status.add_argument("--strict", action="store_true", help="Exit non-zero when status is WARN")
    market_cache_export_status.add_argument("--config", help="Optional config YAML path")
    market_cache_export_status.set_defaults(handler=_handle_market_cache_export_status)

    market_cache_status = subparsers.add_parser(
        "market-cache-status",
        help="Summarize the local market data cache",
    )
    market_cache_status.add_argument("--cache-path", help="Optional market cache CSV path")
    market_cache_status.add_argument("--output-dir", help="Optional market cache report output directory")
    market_cache_status.add_argument("--config", help="Optional config YAML path")
    market_cache_status.set_defaults(handler=_handle_market_cache_status)

    market_cache_preflight = subparsers.add_parser(
        "market-cache-preflight",
        help="Run source-policy-aware checks before market cache ingestion",
    )
    market_cache_preflight.add_argument("--input", required=True, help="Canonical market raw_data.csv path")
    market_cache_preflight.add_argument("--metadata", help="Optional data-source metadata.json path")
    market_cache_preflight.add_argument("--health-metadata", help="Optional data-source health metadata.json path")
    market_cache_preflight.add_argument("--reference-source", help="Optional cached reference source for comparison")
    market_cache_preflight.add_argument("--cache-path", help="Optional market cache CSV path for reference comparison")
    market_cache_preflight.add_argument(
        "--require-fields",
        help="Comma-separated required fields, e.g. close,volume,amount",
    )
    market_cache_preflight.add_argument("--symbol", help="Optional symbol filter")
    market_cache_preflight.add_argument("--start-date", help="Optional inclusive start date")
    market_cache_preflight.add_argument("--end-date", help="Optional inclusive end date")
    market_cache_preflight.add_argument("--strict-provisional", action="store_true", help="Reject provisional fields")
    market_cache_preflight.add_argument("--output-dir", help="Optional preflight report output directory")
    market_cache_preflight.add_argument("--config", help="Optional config YAML path")
    market_cache_preflight.set_defaults(handler=_handle_market_cache_preflight)

    market_daily_update = subparsers.add_parser(
        "market-daily-update",
        help="Run a local preflight-gated market cache update skeleton",
    )
    market_daily_update.add_argument("--symbol-manifest", help="Reviewed CSV manifest of symbols to process")
    market_daily_update.add_argument("--source", help="Data source, e.g. AKSHARE_OPTIONAL")
    market_daily_update.add_argument("--symbol", help="Market symbol, e.g. 000001")
    market_daily_update.add_argument("--start-date", help="Inclusive start date")
    market_daily_update.add_argument("--end-date", help="Inclusive end date")
    market_daily_update.add_argument("--raw-input", help="Existing canonical raw_data.csv path")
    market_daily_update.add_argument("--metadata", help="Optional metadata.json path for raw input")
    market_daily_update.add_argument("--allow-real-data", action="store_true", help="Manual opt-in for real source fetch")
    market_daily_update.add_argument("--dry-run", action="store_true", help="Run without cache write unless --accept-cache-write is also set")
    market_daily_update.add_argument("--accept-cache-write", action="store_true", help="Explicitly allow accepted rows to be ingested into cache")
    market_daily_update.add_argument("--reference-source", help="Optional cached reference source for preflight comparison")
    market_daily_update.add_argument("--require-fields", help="Comma-separated required fields, e.g. close,volume,amount")
    market_daily_update.add_argument("--preferred-upstream", help="Optional preferred upstream, e.g. TENCENT or SINA")
    market_daily_update.add_argument("--strict-provisional", action="store_true", help="Reject provisional fields")
    market_daily_update.add_argument("--fail-fast", action="store_true", help="Stop manifest processing after the first failed row")
    market_daily_update.add_argument("--cache-path", help="Optional market cache CSV path")
    market_daily_update.add_argument("--raw-output-dir", help="Optional raw output root for data-source-fetch")
    market_daily_update.add_argument("--revision-id", help="Optional revision id for fetched raw data")
    market_daily_update.add_argument("--output-dir", help="Optional daily update report output directory")
    market_daily_update.add_argument("--config", help="Optional config YAML path")
    market_daily_update.set_defaults(handler=_handle_market_daily_update)

    historical_backfill = subparsers.add_parser(
        "historical-backfill",
        help="Run a local preflight-gated historical market backfill skeleton",
    )
    historical_backfill.add_argument("--manifest", required=True, help="Reviewed historical backfill CSV manifest")
    historical_backfill.add_argument("--allow-real-data", action="store_true", help="Manual opt-in for real source fetch")
    historical_backfill.add_argument("--dry-run", action="store_true", help="Run without cache write unless --accept-cache-write is also set")
    historical_backfill.add_argument("--accept-cache-write", action="store_true", help="Explicitly allow accepted rows to be ingested into cache")
    historical_backfill.add_argument("--fail-fast", action="store_true", help="Stop after the first failed task")
    historical_backfill.add_argument("--cache-path", help="Optional market cache CSV path")
    historical_backfill.add_argument("--raw-output-dir", help="Optional raw output root for data-source-fetch")
    historical_backfill.add_argument("--output-dir", help="Optional historical backfill report output directory")
    historical_backfill.add_argument("--config", help="Optional config YAML path")
    historical_backfill.set_defaults(handler=_handle_historical_backfill)

    historical_backfill_index = subparsers.add_parser(
        "historical-backfill-index",
        help="Build a local index of historical-backfill artifacts",
    )
    historical_backfill_index.add_argument("--root", help="Historical-backfill artifact root directory")
    historical_backfill_index.add_argument("--output-dir", help="Optional index output directory")
    historical_backfill_index.add_argument("--include-missing-metadata", action="store_true")
    historical_backfill_index.add_argument("--config", help="Optional config YAML path")
    historical_backfill_index.set_defaults(handler=_handle_historical_backfill_index)

    historical_backfill_health = subparsers.add_parser(
        "historical-backfill-health",
        help="Check indexed historical-backfill artifacts",
    )
    historical_backfill_health.add_argument("--index", help="Historical-backfill index CSV path")
    historical_backfill_health.add_argument("--root", help="Historical-backfill artifact root directory")
    historical_backfill_health.add_argument("--output-dir", help="Optional health output directory")
    historical_backfill_health.add_argument("--strict", action="store_true")
    historical_backfill_health.add_argument("--allow-warn", action="store_true")
    historical_backfill_health.add_argument("--config", help="Optional config YAML path")
    historical_backfill_health.set_defaults(handler=_handle_historical_backfill_health)

    historical_backfill_status = subparsers.add_parser(
        "historical-backfill-status",
        help="Summarize the latest local historical-backfill workflow state",
    )
    historical_backfill_status.add_argument("--root", help="Historical-backfill artifact root directory")
    historical_backfill_status.add_argument("--output-dir", help="Optional status output directory")
    historical_backfill_status.add_argument("--strict", action="store_true")
    historical_backfill_status.add_argument("--config", help="Optional config YAML path")
    historical_backfill_status.set_defaults(handler=_handle_historical_backfill_status)

    market_update_handoff = subparsers.add_parser(
        "market-update-handoff",
        help="Convert accepted reviewed offline market update rows into a local snapshot dry run",
    )
    market_update_handoff.add_argument("--symbol-manifest", help="Reviewed offline symbol manifest CSV")
    market_update_handoff.add_argument("--market-daily-update-dir", help="Existing market-daily-update artifact directory")
    market_update_handoff.add_argument("--universe", required=True, help="Universe raw_data.csv path")
    market_update_handoff.add_argument("--trading-calendar", required=True, help="Trading calendar raw_data.csv path")
    market_update_handoff.add_argument("--decision-date", required=True, help="Decision date, e.g. 2024-05-20")
    market_update_handoff.add_argument("--universe-name", required=True, help="Universe name for current-candidates")
    market_update_handoff.add_argument(
        "--selection-profile",
        choices=["default", "demo"],
        default="demo",
        help="Current-candidates selection profile for validation",
    )
    market_update_handoff.add_argument("--top", type=int, help="Candidate count override")
    market_update_handoff.add_argument("--strict-accept-only", action="store_true", help="Exclude WARN_ACCEPT rows")
    market_update_handoff.add_argument("--dry-run", action="store_true", help="Local dry-run; cache is never mutated")
    market_update_handoff.add_argument("--run-pipeline", action="store_true", help="Run data-pipeline/snapshot/current-candidates validation")
    market_update_handoff.add_argument("--skip-validation", action="store_true", help="Only build batch CSV and manifest")
    market_update_handoff.add_argument("--output-dir", help="Optional handoff report output directory")
    market_update_handoff.add_argument("--config", help="Optional config YAML path")
    market_update_handoff.set_defaults(handler=_handle_market_update_handoff)

    market_update_handoff_index = subparsers.add_parser(
        "market-update-handoff-index",
        help="Build a local index of market-update-handoff artifacts",
    )
    market_update_handoff_index.add_argument("--root", help="Market-update-handoff artifact root directory")
    market_update_handoff_index.add_argument("--output-dir", help="Optional index output directory")
    market_update_handoff_index.add_argument("--include-missing-metadata", action="store_true")
    market_update_handoff_index.add_argument("--config", help="Optional config YAML path")
    market_update_handoff_index.set_defaults(handler=_handle_market_update_handoff_index)

    market_update_handoff_health = subparsers.add_parser(
        "market-update-handoff-health",
        help="Check indexed market-update-handoff artifacts",
    )
    market_update_handoff_health.add_argument("--index", help="Market-update-handoff index CSV path")
    market_update_handoff_health.add_argument("--root", help="Market-update-handoff artifact root directory")
    market_update_handoff_health.add_argument("--output-dir", help="Optional health output directory")
    market_update_handoff_health.add_argument("--strict", action="store_true")
    market_update_handoff_health.add_argument("--allow-warn", action="store_true")
    market_update_handoff_health.add_argument("--config", help="Optional config YAML path")
    market_update_handoff_health.set_defaults(handler=_handle_market_update_handoff_health)

    market_update_handoff_status = subparsers.add_parser(
        "market-update-handoff-status",
        help="Summarize the latest local market-update-handoff workflow state",
    )
    market_update_handoff_status.add_argument("--root", help="Market-update-handoff artifact root directory")
    market_update_handoff_status.add_argument("--output-dir", help="Optional status output directory")
    market_update_handoff_status.add_argument("--strict", action="store_true")
    market_update_handoff_status.add_argument("--config", help="Optional config YAML path")
    market_update_handoff_status.set_defaults(handler=_handle_market_update_handoff_status)

    market_cache_compare = subparsers.add_parser(
        "market-cache-compare",
        help="Compare cached market bars between two local data sources",
    )
    market_cache_compare.add_argument("--symbol", required=True, help="Symbol to compare, e.g. 000001")
    market_cache_compare.add_argument("--source-a", required=True, help="First source, e.g. AKSHARE_OPTIONAL")
    market_cache_compare.add_argument("--source-b", required=True, help="Second source, e.g. BAOSTOCK_OPTIONAL")
    market_cache_compare.add_argument("--start-date", help="Optional inclusive start date")
    market_cache_compare.add_argument("--end-date", help="Optional inclusive end date")
    market_cache_compare.add_argument("--cache-path", help="Optional market cache CSV path")
    market_cache_compare.add_argument("--output-dir", help="Optional comparison report output directory")
    market_cache_compare.add_argument("--config", help="Optional config YAML path")
    market_cache_compare.set_defaults(handler=_handle_market_cache_compare)

    market_source_policy = subparsers.add_parser(
        "market-source-policy",
        help="Write the market source field reliability policy table",
    )
    market_source_policy.add_argument("--output-dir", help="Optional policy report output directory")
    market_source_policy.add_argument("--config", help="Optional config YAML path")
    market_source_policy.set_defaults(handler=_handle_market_source_policy)

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


def _handle_current_candidates_backfill_plan(args: argparse.Namespace) -> int:
    result = build_current_candidates_backfill_plan(
        cache_path=args.cache_path,
        start_date=args.start_date,
        end_date=args.end_date,
        universe=args.universe,
        selection_profile=args.selection_profile,
        horizons=_parse_int_values(args.horizons),
        max_dates=args.max_dates,
        warmup_trading_days=args.warmup_trading_days,
        min_symbol_coverage=args.min_symbol_coverage,
        source_policy=args.source_policy,
        output_dir=args.output_dir,
    )
    print(f"plan_id: {result.plan_id}")
    print(f"status: {result.status}")
    print(f"selected_date_count: {result.selected_date_count}")
    print(f"first_signal_date: {result.first_signal_date}")
    print(f"last_signal_date: {result.last_signal_date}")
    print(f"warmup_trading_days: {result.request.warmup_trading_days}")
    print("warmup_feasibility_counts:")
    for key, value in result.warmup_feasibility_counts.items():
        print(f"  {key}: {value}")
    print("horizon_feasibility_counts:")
    for key, value in result.horizon_feasibility_counts.items():
        print(f"  {key}: {value}")
    print(f"plan_path: {result.artifact_paths['plan_csv']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, message delivery, or network/API call was invoked.")
    return 0


def _handle_current_candidates_backfill_plan_index(args: argparse.Namespace) -> int:
    result = build_current_candidates_backfill_plan_index(
        root=args.root,
        output_dir=args.output_dir,
        include_missing_metadata=bool(args.include_missing_metadata),
    )
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index CSV path: {result.artifact_paths['current_candidates_backfill_plan_index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, message delivery, or network/API call was invoked.")
    return 0


def _handle_current_candidates_backfill_plan_health(args: argparse.Namespace) -> int:
    result = check_current_candidates_backfill_plan_health(
        index_path=args.index,
        root=args.root,
        output_dir=args.output_dir,
    )
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Health report path: {result.artifact_paths['current_candidates_backfill_plan_health_report']}")
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"latest_plan_id: {summary.get('latest_plan_id', '')}")
    print(f"latest_plan_is_warmup_aware: {summary.get('latest_plan_is_warmup_aware', '')}")
    print(f"active_plan_health_status: {summary.get('active_plan_health_status', '')}")
    print(f"active_plan_issue_count: {summary.get('active_plan_issue_count', '')}")
    print(f"active_plan_error_count: {summary.get('active_plan_error_count', '')}")
    print(f"legacy_plan_count: {summary.get('legacy_plan_count', '')}")
    print(f"legacy_missing_warmup_count: {summary.get('legacy_missing_warmup_count', '')}")
    print(f"stale_plan_warning_count: {summary.get('stale_plan_warning_count', '')}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, message delivery, or network/API call was invoked.")
    return 0


def _handle_current_candidates_backfill_plan_status(args: argparse.Namespace) -> int:
    result = run_current_candidates_backfill_plan_status(root=args.root, output_dir=args.output_dir)
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Status report path: {result.artifact_paths['current_candidates_backfill_plan_status_report']}")
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_plan_id: {result.latest_plan_id}")
    print(f"health_status: {result.health_status}")
    print(f"selected_date_count: {result.selected_date_count}")
    print(f"first_signal_date: {summary.get('first_signal_date', '')}")
    print(f"last_signal_date: {summary.get('last_signal_date', '')}")
    print(f"warmup_trading_days: {summary.get('warmup_trading_days', '')}")
    print(f"warmup_feasible_count: {summary.get('warmup_feasible_count', '')}")
    print(f"forward_1d_available_count: {summary.get('forward_1d_available_count', '')}")
    print(f"forward_3d_available_count: {summary.get('forward_3d_available_count', '')}")
    print(f"forward_5d_available_count: {summary.get('forward_5d_available_count', '')}")
    print(f"forward_10d_available_count: {summary.get('forward_10d_available_count', '')}")
    print(f"latest_plan_is_warmup_aware: {summary.get('latest_plan_is_warmup_aware', '')}")
    print(f"overall_health_status: {summary.get('overall_health_status', '')}")
    print(f"active_plan_issue_count: {summary.get('active_plan_issue_count', '')}")
    print(f"active_plan_error_count: {summary.get('active_plan_error_count', '')}")
    print(f"legacy_plan_count: {summary.get('legacy_plan_count', '')}")
    print(f"legacy_missing_warmup_count: {summary.get('legacy_missing_warmup_count', '')}")
    print(f"stale_plan_warning_count: {summary.get('stale_plan_warning_count', '')}")
    print(f"next_manual_action: {result.next_manual_action}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, message delivery, or network/API call was invoked.")
    return 0


def _handle_current_candidates_backfill_execution_manifest(args: argparse.Namespace) -> int:
    result = build_current_candidates_backfill_execution_manifest(
        plan=args.plan,
        snapshot_root=args.snapshot_root,
        snapshot_quality_root=args.snapshot_quality_root,
        universe_root=args.universe_root,
        selection_profile=args.selection_profile,
        output_dir=args.output_dir,
    )
    print(f"execution_manifest_id: {result.execution_manifest_id}")
    print(f"status: {result.status}")
    print(f"row_count: {result.row_count}")
    print(f"ready_count: {result.ready_count}")
    print(f"blocked_count: {result.blocked_count}")
    print("readiness_counts:")
    for status, count in result.readiness_counts.items():
        print(f"  {status}={count}")
    print(f"manifest_path: {result.artifact_paths['execution_manifest_csv']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
        "order placement, message delivery, or network/API call was invoked."
    )
    return 0


def _handle_pit_universe_overlay_plan(args: argparse.Namespace) -> int:
    result = build_point_in_time_universe_overlay_plan(
        execution_manifest=args.execution_manifest,
        base_universe=args.base_universe,
        universe_name=args.universe_name,
        allow_template_include=bool(args.allow_template_include),
        output_dir=args.output_dir,
    )
    print(f"overlay_plan_id: {result.overlay_plan_id}")
    print(f"status: {result.status}")
    print(f"row_count: {result.row_count}")
    print(f"signal_date_count: {result.signal_date_count}")
    print(f"symbol_count: {result.symbol_count}")
    print("review_status_counts:")
    for status, count in result.review_status_counts.items():
        print(f"  {status}={count}")
    print(f"survivorship_bias_warning_count: {result.survivorship_bias_warning_count}")
    print(f"valid_for_signal_date_count: {result.valid_for_signal_date_count}")
    print(f"plan_path: {result.artifact_paths['overlay_plan_csv']}")
    print(f"template_path: {result.artifact_paths['overlay_template_csv']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
        "order placement, message delivery, LLM API, or external API was invoked."
    )
    return 0


def _handle_pit_universe_overlay_plan_index(args: argparse.Namespace) -> int:
    result = build_point_in_time_universe_overlay_plan_index(
        root=args.root,
        output_dir=args.output_dir,
        include_missing_metadata=bool(args.include_missing_metadata),
    )
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index CSV path: {result.artifact_paths['point_in_time_universe_overlay_plan_index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
        "order placement, message delivery, LLM API, or external API was invoked."
    )
    return 0


def _handle_pit_universe_overlay_plan_health(args: argparse.Namespace) -> int:
    result = check_point_in_time_universe_overlay_plan_health(
        index_path=args.index,
        root=args.root,
        output_dir=args.output_dir,
    )
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Health report path: {result.artifact_paths['point_in_time_universe_overlay_plan_health_report']}")
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
        "order placement, message delivery, LLM API, or external API was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_pit_universe_overlay_plan_status(args: argparse.Namespace) -> int:
    result = run_point_in_time_universe_overlay_plan_status(root=args.root, output_dir=args.output_dir)
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Status report path: {result.artifact_paths['point_in_time_universe_overlay_plan_status_report']}")
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_overlay_plan_id: {result.latest_overlay_plan_id}")
    print(f"health_status: {result.health_status}")
    print(f"row_count: {result.row_count}")
    print(f"signal_date_count: {summary.get('signal_date_count', '')}")
    print(f"symbol_count: {summary.get('symbol_count', '')}")
    print(f"needs_manual_review_count: {result.needs_manual_review_count}")
    print(f"valid_for_signal_date_count: {result.valid_for_signal_date_count}")
    print(f"survivorship_bias_warning_count: {summary.get('survivorship_bias_warning_count', '')}")
    print(f"next_manual_action: {result.next_manual_action}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
        "order placement, message delivery, LLM API, or external API was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_pit_universe_overlay_review(args: argparse.Namespace) -> int:
    result = build_pit_universe_overlay_review(
        overlay_plan=args.overlay_plan,
        review_updates=args.review_updates,
        write_review_template_only=bool(args.write_review_template_only),
        output_dir=args.output_dir,
    )
    print(f"review_id: {result.review_id}")
    print(f"status: {result.status}")
    print(f"row_count: {result.row_count}")
    print(f"approved_count: {result.approved_count}")
    print(f"rejected_count: {result.rejected_count}")
    print(f"needs_more_evidence_count: {result.needs_more_evidence_count}")
    print(f"needs_manual_review_count: {result.needs_manual_review_count}")
    print(f"valid_for_signal_date_count: {result.valid_for_signal_date_count}")
    print(f"reviewed_overlay_path: {result.artifact_paths['reviewed_overlay']}")
    print(f"review_template_path: {result.artifact_paths['review_template']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
        "order placement, message delivery, LLM API, or external API was invoked."
    )
    return 0


def _handle_pit_universe_overlay_review_index(args: argparse.Namespace) -> int:
    result = build_pit_universe_overlay_review_index(
        root=args.root,
        output_dir=args.output_dir,
        include_missing_metadata=bool(args.include_missing_metadata),
    )
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index CSV path: {result.artifact_paths['pit_universe_overlay_review_index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
        "order placement, message delivery, LLM API, or external API was invoked."
    )
    return 0


def _handle_pit_universe_overlay_review_health(args: argparse.Namespace) -> int:
    result = check_pit_universe_overlay_review_health(
        index_path=args.index,
        root=args.root,
        output_dir=args.output_dir,
    )
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Health report path: {result.artifact_paths['pit_universe_overlay_review_health_report']}")
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
        "order placement, message delivery, LLM API, or external API was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_pit_universe_overlay_review_status(args: argparse.Namespace) -> int:
    result = run_pit_universe_overlay_review_status(root=args.root, output_dir=args.output_dir)
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Status report path: {result.artifact_paths['pit_universe_overlay_review_status_report']}")
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_review_id: {result.latest_review_id}")
    print(f"health_status: {result.health_status}")
    print(f"approved_count: {result.approved_count}")
    print(f"valid_for_signal_date_count: {result.valid_for_signal_date_count}")
    print(f"needs_more_evidence_count: {result.needs_more_evidence_count}")
    print(f"unresolved_survivorship_warning_count: {result.unresolved_survivorship_warning_count}")
    print(f"report_path: {summary.get('report_path', '')}")
    print(f"next_manual_action: {result.next_manual_action}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
        "order placement, message delivery, LLM API, or external API was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_pit_universe_overlay_export_readiness(args: argparse.Namespace) -> int:
    result = build_pit_universe_overlay_export_readiness(
        review=args.review,
        output_dir=args.output_dir,
    )
    print(f"export_readiness_id: {result.export_readiness_id}")
    print(f"status: {result.status}")
    print(f"readiness_status: {result.readiness_status}")
    print(f"row_count: {result.row_count}")
    print(f"approved_count: {result.approved_count}")
    print(f"export_ready_count: {result.export_ready_count}")
    print(f"blocked_count: {result.blocked_count}")
    print(f"unresolved_survivorship_warning_count: {result.unresolved_survivorship_warning_count}")
    print(f"missing_required_columns_count: {result.missing_required_columns_count}")
    print(f"duplicate_key_count: {result.duplicate_key_count}")
    print(f"readiness_csv_path: {result.artifact_paths['readiness_csv']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, "
        "LLM/API, external API, or cache mutation was invoked."
    )
    return 0


def _handle_pit_universe_overlay_export_readiness_index(args: argparse.Namespace) -> int:
    result = build_pit_universe_overlay_export_readiness_index(
        root=args.root,
        output_dir=args.output_dir,
        include_missing_metadata=bool(args.include_missing_metadata),
    )
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Index CSV path: "
        f"{result.artifact_paths['pit_universe_overlay_export_readiness_index_csv']}"
    )
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, "
        "LLM/API, external API, or cache mutation was invoked."
    )
    return 0


def _handle_pit_universe_overlay_export_readiness_health(args: argparse.Namespace) -> int:
    result = check_pit_universe_overlay_export_readiness_health(
        index_path=args.index,
        root=args.root,
        output_dir=args.output_dir,
    )
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Health report path: "
        f"{result.artifact_paths['pit_universe_overlay_export_readiness_health_report']}"
    )
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, "
        "LLM/API, external API, or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_pit_universe_overlay_export_readiness_status(args: argparse.Namespace) -> int:
    result = run_pit_universe_overlay_export_readiness_status(root=args.root, output_dir=args.output_dir)
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Status report path: "
        f"{result.artifact_paths['pit_universe_overlay_export_readiness_status_report']}"
    )
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_export_readiness_id: {result.latest_export_readiness_id}")
    print(f"health_status: {result.health_status}")
    print(f"review_id: {result.review_id}")
    print(f"approved_count: {result.approved_count}")
    print(f"export_ready_count: {result.export_ready_count}")
    print(f"blocked_count: {result.blocked_count}")
    print(f"no_approved_rows: {result.no_approved_rows}")
    print(f"missing_required_columns_count: {result.missing_required_columns_count}")
    print(f"unresolved_survivorship_warning_count: {result.unresolved_survivorship_warning_count}")
    print(f"report_path: {summary.get('report_path', '')}")
    print(f"next_manual_action: {result.next_manual_action}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, "
        "LLM/API, external API, or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_pit_universe_export_staging(args: argparse.Namespace) -> int:
    result = build_pit_universe_export_staging(
        export_readiness=args.export_readiness,
        output_dir=args.output_dir,
        allow_diagnostic_source=bool(args.allow_diagnostic_source),
    )
    print(f"staging_id: {result.staging_id}")
    print(f"status: {result.status}")
    print(f"staging_status: {result.staging_status}")
    print(f"row_count: {result.row_count}")
    print(f"export_ready_input_count: {result.export_ready_input_count}")
    print(f"staged_row_count: {result.staged_row_count}")
    print(f"blocked_count: {result.blocked_count}")
    print(f"source_is_diagnostic: {result.source_is_diagnostic}")
    print(f"no_ready_rows: {result.no_ready_rows}")
    print(f"duplicate_key_count: {result.duplicate_key_count}")
    print(f"missing_required_columns_count: {result.missing_required_columns_count}")
    print(f"staging_csv_path: {result.artifact_paths['staging_csv']}")
    print(f"combined_preview_csv_path: {result.artifact_paths['combined_preview_csv']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No data/raw write, data/processed write, current-candidates generation, snapshot build, "
        "forward labels, live trading, broker API, order placement, message delivery, network/API, "
        "LLM/API, or cache mutation was invoked."
    )
    return 0


def _handle_pit_universe_export_staging_index(args: argparse.Namespace) -> int:
    result = build_pit_universe_export_staging_index(
        root=args.root,
        output_dir=args.output_dir,
        include_missing_metadata=bool(args.include_missing_metadata),
    )
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index CSV path: {result.artifact_paths['pit_universe_export_staging_index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No data/raw write, data/processed write, current-candidates generation, snapshot build, "
        "forward labels, live trading, broker API, order placement, message delivery, network/API, "
        "LLM/API, or cache mutation was invoked."
    )
    return 0


def _handle_pit_universe_export_staging_health(args: argparse.Namespace) -> int:
    result = check_pit_universe_export_staging_health(
        index_path=args.index,
        root=args.root,
        output_dir=args.output_dir,
    )
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Health report path: {result.artifact_paths['pit_universe_export_staging_health_report']}")
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(
        "No data/raw write, data/processed write, current-candidates generation, snapshot build, "
        "forward labels, live trading, broker API, order placement, message delivery, network/API, "
        "LLM/API, or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_pit_universe_export_staging_status(args: argparse.Namespace) -> int:
    result = run_pit_universe_export_staging_status(root=args.root, output_dir=args.output_dir)
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Status report path: {result.artifact_paths['pit_universe_export_staging_status_report']}")
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_staging_id: {result.latest_staging_id}")
    print(f"health_status: {result.health_status}")
    print(f"export_readiness_id: {result.export_readiness_id}")
    print(f"review_id: {result.review_id}")
    print(f"export_ready_input_count: {result.export_ready_input_count}")
    print(f"staged_row_count: {result.staged_row_count}")
    print(f"blocked_count: {result.blocked_count}")
    print(f"source_is_diagnostic: {result.source_is_diagnostic}")
    print(f"no_ready_rows: {result.no_ready_rows}")
    print(f"report_path: {summary.get('report_path', '')}")
    print(f"next_manual_action: {result.next_manual_action}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No data/raw write, data/processed write, current-candidates generation, snapshot build, "
        "forward labels, live trading, broker API, order placement, message delivery, network/API, "
        "LLM/API, or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_pit_universe_evidence_completion_helper(args: argparse.Namespace) -> int:
    result = build_pit_universe_evidence_completion_helper(
        review=args.review,
        base_universe=args.base_universe,
        output_dir=args.output_dir,
    )
    print(f"helper_id: {result.helper_id}")
    print(f"status: {result.status}")
    print(f"row_count: {result.row_count}")
    print(f"needs_evidence_count: {result.needs_evidence_count}")
    print(f"rows_with_base_hints_count: {result.rows_with_base_hints_count}")
    print(f"future_dated_hint_count: {result.future_dated_hint_count}")
    print(f"authoritative_hint_count: {result.authoritative_hint_count}")
    print(f"approved_count: {result.approved_count}")
    print(f"valid_for_signal_date_count: {result.valid_for_signal_date_count}")
    print(f"evidence_completion_template_path: {result.artifact_paths['evidence_completion_template']}")
    print(f"gap_report_path: {result.artifact_paths['gap_report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, "
        "network/API, LLM/API, or cache mutation was invoked."
    )
    return 0


def _handle_pit_universe_evidence_review_worklist(args: argparse.Namespace) -> int:
    result = build_pit_universe_evidence_review_worklist(
        helper=args.helper,
        review=args.review,
        output_dir=args.output_dir,
    )
    print(f"worklist_id: {result.worklist_id}")
    print(f"status: {result.status}")
    print(f"row_count: {result.row_count}")
    print(f"symbol_count: {result.symbol_count}")
    print(f"signal_date_count: {result.signal_date_count}")
    print(f"needs_manual_review_count: {result.needs_manual_review_count}")
    print(f"needs_evidence_count: {result.needs_evidence_count}")
    print(f"future_dated_hint_count: {result.future_dated_hint_count}")
    print(f"authoritative_hint_count: {result.authoritative_hint_count}")
    print(f"approved_count: {result.approved_count}")
    print(f"valid_for_signal_date_count: {result.valid_for_signal_date_count}")
    print(f"worklist_csv_path: {result.artifact_paths['worklist_csv']}")
    print(f"symbol_summary_path: {result.artifact_paths['symbol_summary']}")
    print(f"date_summary_path: {result.artifact_paths['date_summary']}")
    print(f"update_template_path: {result.artifact_paths['update_template']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, "
        "network/API, LLM/API, or cache mutation was invoked."
    )
    return 0


def _handle_pit_universe_evidence_review_worklist_index(args: argparse.Namespace) -> int:
    result = build_pit_universe_evidence_review_worklist_index(
        root=args.root,
        output_dir=args.output_dir,
        include_missing_metadata=bool(args.include_missing_metadata),
    )
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Index CSV path: "
        f"{result.artifact_paths['pit_universe_evidence_review_worklist_index_csv']}"
    )
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, "
        "LLM/API, external API, or cache mutation was invoked."
    )
    return 0


def _handle_pit_universe_evidence_review_worklist_health(args: argparse.Namespace) -> int:
    result = check_pit_universe_evidence_review_worklist_health(
        index_path=args.index,
        root=args.root,
        output_dir=args.output_dir,
    )
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Health report path: "
        f"{result.artifact_paths['pit_universe_evidence_review_worklist_health_report']}"
    )
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, "
        "LLM/API, external API, or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_pit_universe_evidence_review_worklist_status(args: argparse.Namespace) -> int:
    result = run_pit_universe_evidence_review_worklist_status(root=args.root, output_dir=args.output_dir)
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Status report path: "
        f"{result.artifact_paths['pit_universe_evidence_review_worklist_status_report']}"
    )
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_worklist_id: {result.latest_worklist_id}")
    print(f"health_status: {result.health_status}")
    print(f"review_id: {result.review_id}")
    print(f"helper_id: {result.helper_id}")
    print(f"row_count: {result.row_count}")
    print(f"symbol_count: {result.symbol_count}")
    print(f"signal_date_count: {result.signal_date_count}")
    print(f"needs_evidence_count: {result.needs_evidence_count}")
    print(f"future_dated_hint_count: {result.future_dated_hint_count}")
    print(f"authoritative_hint_count: {result.authoritative_hint_count}")
    print(f"report_path: {summary.get('report_path', '')}")
    print(f"next_manual_action: {result.next_manual_action}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, "
        "LLM/API, external API, or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_pit_universe_evidence_update_ingestion(args: argparse.Namespace) -> int:
    result = build_pit_universe_evidence_update_ingestion(
        completed_updates=args.completed_updates,
        worklist=args.worklist,
        output_dir=args.output_dir,
    )
    print(f"ingestion_id: {result.ingestion_id}")
    print(f"status: {result.status}")
    print(f"row_count: {result.row_count}")
    print(f"ready_for_review_update_count: {result.ready_for_review_update_count}")
    print(f"blocked_count: {result.blocked_count}")
    print(f"approval_requested_count: {result.approval_requested_count}")
    print(f"approved_ready_count: {result.approved_ready_count}")
    print(f"rejected_ready_count: {result.rejected_ready_count}")
    print(f"needs_more_evidence_ready_count: {result.needs_more_evidence_ready_count}")
    print(f"duplicate_identity_count: {result.duplicate_identity_count}")
    print(f"missing_identity_count: {result.missing_identity_count}")
    print(f"suggested_copy_risk_count: {result.suggested_copy_risk_count}")
    print(f"ingestion_csv_path: {result.artifact_paths['ingestion_csv']}")
    print(f"review_updates_path: {result.artifact_paths['review_updates']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval was applied, no universe export, data/raw write, data/processed write, "
        "current-candidates generation, snapshot build, forward labels, live trading, broker API, "
        "order placement, message delivery, network/API, LLM/API, or cache mutation was invoked."
    )
    return 0


def _handle_pit_universe_evidence_update_ingestion_index(args: argparse.Namespace) -> int:
    result = build_pit_universe_evidence_update_ingestion_index(
        root=args.root,
        output_dir=args.output_dir,
        include_missing_metadata=bool(args.include_missing_metadata),
    )
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Index CSV path: "
        f"{result.artifact_paths['pit_universe_evidence_update_ingestion_index_csv']}"
    )
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval applied, universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, "
        "external API, or cache mutation was invoked."
    )
    return 0


def _handle_pit_universe_evidence_update_ingestion_health(args: argparse.Namespace) -> int:
    result = check_pit_universe_evidence_update_ingestion_health(
        index_path=args.index,
        root=args.root,
        output_dir=args.output_dir,
    )
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Health report path: "
        f"{result.artifact_paths['pit_universe_evidence_update_ingestion_health_report']}"
    )
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval applied, universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, "
        "external API, or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_pit_universe_evidence_update_ingestion_status(args: argparse.Namespace) -> int:
    result = run_pit_universe_evidence_update_ingestion_status(root=args.root, output_dir=args.output_dir)
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Status report path: "
        f"{result.artifact_paths['pit_universe_evidence_update_ingestion_status_report']}"
    )
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_ingestion_id: {result.latest_ingestion_id}")
    print(f"health_status: {result.health_status}")
    print(f"row_count: {result.row_count}")
    print(f"ready_for_review_update_count: {result.ready_for_review_update_count}")
    print(f"blocked_count: {result.blocked_count}")
    print(f"approval_requested_count: {result.approval_requested_count}")
    print(f"approved_ready_count: {result.approved_ready_count}")
    print(f"duplicate_identity_count: {result.duplicate_identity_count}")
    print(f"suggested_copy_risk_count: {result.suggested_copy_risk_count}")
    print(f"report_path: {summary.get('report_path', '')}")
    print(f"review_updates_path: {summary.get('review_updates_path', '')}")
    print(f"next_manual_action: {result.next_manual_action}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval applied, universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, "
        "external API, or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_pit_evidence_checklist_validator(args: argparse.Namespace) -> int:
    result = build_pit_evidence_checklist_validator(
        completed_updates=args.completed_updates,
        stock_checklist=args.stock_checklist,
        etf_checklist=args.etf_checklist,
        source_acceptance=args.source_acceptance,
        output_dir=args.output_dir,
    )
    print(f"validator_id: {result.validator_id}")
    print(f"status: {result.status}")
    print(f"row_count: {result.row_count}")
    print(f"checklist_pass_count: {result.checklist_pass_count}")
    print(f"blocked_count: {result.blocked_count}")
    print(f"stock_core_blocked_count: {result.stock_core_blocked_count}")
    print(f"etf_core_blocked_count: {result.etf_core_blocked_count}")
    print(f"validation_csv_path: {result.artifact_paths['validation_csv']}")
    print(f"summary_csv_path: {result.artifact_paths['summary_csv']}")
    print(f"missing_evidence_matrix_path: {result.artifact_paths['missing_evidence_matrix']}")
    print(f"approval_candidate_preview_path: {result.artifact_paths['approval_candidate_preview']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print(
        "No approval applied, PIT review, export-readiness, staging, universe export, active mutation, "
        "data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked."
    )
    return 0


def _handle_pit_evidence_checklist_validator_index(args: argparse.Namespace) -> int:
    result = build_pit_evidence_checklist_validator_index(root=args.root, output_dir=args.output_dir)
    print(f"Index artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Index CSV path: {result['artifact_paths']['index_csv']}")
    print(f"artifact_count: {result['artifact_count']}")
    print(
        "No approval applied, PIT review, export-readiness, staging, universe export, active mutation, "
        "data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked."
    )
    return 0


def _handle_pit_evidence_checklist_validator_health(args: argparse.Namespace) -> int:
    result = check_pit_evidence_checklist_validator_health(root=args.root, output_dir=args.output_dir)
    print(f"Health artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Health report path: {result['artifact_paths']['report']}")
    print(f"Health status: {result['status']}")
    print(f"checked_artifact_count: {result['checked_artifact_count']}")
    print(f"issue_count: {result['issue_count']}")
    print(f"error_count: {result['error_count']}")
    print(f"warning_count: {result['warning_count']}")
    print(
        "No approval applied, PIT review, export-readiness, staging, universe export, active mutation, "
        "data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked."
    )
    return 1 if result["status"] == "FAIL" else 0


def _handle_pit_evidence_checklist_validator_status(args: argparse.Namespace) -> int:
    result = run_pit_evidence_checklist_validator_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Status report path: {result['artifact_paths']['report']}")
    print(f"status: {result['status']}")
    print(f"workflow_stage: {result['workflow_stage']}")
    print(f"latest_validator_id: {result['latest_validator_id']}")
    print(f"health_status: {result['health_status']}")
    print(f"row_count: {result['row_count']}")
    print(f"checklist_pass_count: {result['checklist_pass_count']}")
    print(f"blocked_count: {result['blocked_count']}")
    print(f"stock_core_blocked_count: {result['stock_core_blocked_count']}")
    print(f"etf_core_blocked_count: {result['etf_core_blocked_count']}")
    print(f"report_path: {result['report_path']}")
    print(f"next_manual_action: {result['next_manual_action']}")
    print(
        "No approval applied, PIT review, export-readiness, staging, universe export, active mutation, "
        "data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked."
    )
    return 1 if result["status"] == "FAIL" else 0


def _handle_pit_evidence_policy_profile_comparison(args: argparse.Namespace) -> int:
    result = build_pit_evidence_policy_profile_comparison(
        validator=args.validator,
        completed_updates=args.completed_updates,
        policy_audit=args.policy_audit,
        profile=args.profile,
        decision_policy=args.decision_policy,
        decision_time=args.decision_time,
        output_dir=args.output_dir,
    )
    print(f"comparison_id: {result.comparison_id}")
    print(f"status: {result.status}")
    print(f"reference_profile_name: {result.reference_profile_name}")
    print(f"profile_name: {result.profile_name}")
    print(f"profile_is_opt_in: {result.profile_is_opt_in}")
    print(f"strict_default_unchanged: {result.strict_default_unchanged}")
    print(f"row_count: {result.row_count}")
    print(f"strict_checklist_pass_count: {result.strict_checklist_pass_count}")
    print(f"eod_low_budget_checklist_pass_count: {result.eod_low_budget_checklist_pass_count}")
    print(f"reviewed_no_hit_support_pass_count: {result.reviewed_no_hit_support_pass_count}")
    print(f"no_hit_context_supported_count: {result.no_hit_context_supported_count}")
    print(f"reviewer_acceptance_required_count: {result.reviewer_acceptance_required_count}")
    print(f"relaxed_blocker_count: {result.relaxed_blocker_count}")
    print(f"remaining_blocked_count: {result.remaining_blocked_count}")
    print(f"comparison_csv_path: {result.artifact_paths['comparison_csv']}")
    print(f"summary_csv_path: {result.artifact_paths['summary_csv']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print(
        "No approval applied, PIT review, export-readiness, staging, universe export, active mutation, "
        "data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked."
    )
    return 0


def _handle_pit_evidence_policy_profile_comparison_index(args: argparse.Namespace) -> int:
    result = build_pit_evidence_policy_profile_comparison_index(root=args.root, output_dir=args.output_dir)
    print(f"Index artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Index CSV path: {result['artifact_paths']['index_csv']}")
    print(f"artifact_count: {result['artifact_count']}")
    print(
        "No approval applied, PIT review, export-readiness, staging, universe export, active mutation, "
        "data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked."
    )
    return 0


def _handle_pit_evidence_policy_profile_comparison_health(args: argparse.Namespace) -> int:
    result = check_pit_evidence_policy_profile_comparison_health(root=args.root, output_dir=args.output_dir)
    print(f"Health artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Health report path: {result['artifact_paths']['report']}")
    print(f"Health status: {result['status']}")
    print(f"checked_artifact_count: {result['checked_artifact_count']}")
    print(f"issue_count: {result['issue_count']}")
    print(f"error_count: {result['error_count']}")
    print(f"warning_count: {result['warning_count']}")
    print(
        "No approval applied, PIT review, export-readiness, staging, universe export, active mutation, "
        "data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked."
    )
    return 1 if result["status"] == "FAIL" else 0


def _handle_pit_evidence_policy_profile_comparison_status(args: argparse.Namespace) -> int:
    result = run_pit_evidence_policy_profile_comparison_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Status report path: {result['artifact_paths']['report']}")
    print(f"status: {result['status']}")
    print(f"workflow_stage: {result['workflow_stage']}")
    print(f"latest_comparison_id: {result['latest_comparison_id']}")
    print(f"health_status: {result['health_status']}")
    print(f"profile_name: {result['profile_name']}")
    print(f"row_count: {result['row_count']}")
    print(f"strict_checklist_pass_count: {result['strict_checklist_pass_count']}")
    print(f"eod_low_budget_checklist_pass_count: {result['eod_low_budget_checklist_pass_count']}")
    print(f"reviewed_no_hit_support_pass_count: {result['reviewed_no_hit_support_pass_count']}")
    print(f"no_hit_context_supported_count: {result['no_hit_context_supported_count']}")
    print(f"reviewer_acceptance_required_count: {result['reviewer_acceptance_required_count']}")
    print(f"relaxed_blocker_count: {result['relaxed_blocker_count']}")
    print(f"remaining_blocked_count: {result['remaining_blocked_count']}")
    print(f"report_path: {result['report_path']}")
    print(f"next_manual_action: {result['next_manual_action']}")
    print(
        "No approval applied, PIT review, export-readiness, staging, universe export, active mutation, "
        "data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked."
    )
    return 1 if result["status"] == "FAIL" else 0


def _handle_pit_official_status_evidence_packet(args: argparse.Namespace) -> int:
    result = build_pit_official_status_evidence_packet(
        source_smoke_root=args.source_smoke_root,
        non_relaxed_root=args.non_relaxed_root,
        policy_comparison=args.policy_comparison,
        validator=args.validator,
        activated_plan=args.activated_plan,
        stock_checklist=args.stock_checklist,
        etf_checklist=args.etf_checklist,
        source_acceptance=args.source_acceptance,
        output_dir=args.output_dir,
    )
    print(f"packet_id: {result.packet_id}")
    print(f"status: {result.status}")
    print(f"row_count: {result.row_count}")
    print(f"evidence_packet_row_count: {result.evidence_packet_row_count}")
    print(f"strong_official_date_specific_count: {result.strong_official_date_specific_count}")
    print(f"supporting_official_symbol_level_count: {result.supporting_official_symbol_level_count}")
    print(f"supporting_local_eod_cache_count: {result.supporting_local_eod_cache_count}")
    print(f"context_only_count: {result.context_only_count}")
    print(f"missing_count: {result.missing_count}")
    print(f"checklist_pass_count: {result.checklist_pass_count}")
    print(f"blocked_count: {result.blocked_count}")
    print(f"eod_low_budget_checklist_pass_count: {result.eod_low_budget_checklist_pass_count}")
    print(f"packet_csv_path: {result.artifact_paths['packet_csv']}")
    print(f"updated_draft_completed_updates_path: {result.artifact_paths['updated_draft_completed_updates']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print(
        "No approval applied, PIT review, export-readiness, staging, universe export, active mutation, "
        "data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked."
    )
    return 0


def _handle_pit_official_status_evidence_packet_index(args: argparse.Namespace) -> int:
    result = build_pit_official_status_evidence_packet_index(root=args.root, output_dir=args.output_dir)
    print(f"Index artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Index CSV path: {result['artifact_paths']['index_csv']}")
    print(f"artifact_count: {result['artifact_count']}")
    print(
        "No approval applied, PIT review, export-readiness, staging, universe export, active mutation, "
        "data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked."
    )
    return 0


def _handle_pit_official_status_evidence_packet_health(args: argparse.Namespace) -> int:
    result = check_pit_official_status_evidence_packet_health(root=args.root, output_dir=args.output_dir)
    print(f"Health artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Health report path: {result['artifact_paths']['report']}")
    print(f"Health status: {result['status']}")
    print(f"checked_artifact_count: {result['checked_artifact_count']}")
    print(f"issue_count: {result['issue_count']}")
    print(f"error_count: {result['error_count']}")
    print(f"warning_count: {result['warning_count']}")
    print(
        "No approval applied, PIT review, export-readiness, staging, universe export, active mutation, "
        "data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked."
    )
    return 1 if result["status"] == "FAIL" else 0


def _handle_pit_official_status_evidence_packet_status(args: argparse.Namespace) -> int:
    result = run_pit_official_status_evidence_packet_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Status report path: {result['artifact_paths']['report']}")
    print(f"status: {result['status']}")
    print(f"workflow_stage: {result['workflow_stage']}")
    print(f"latest_packet_id: {result['latest_packet_id']}")
    print(f"health_status: {result['health_status']}")
    print(f"row_count: {result['row_count']}")
    print(f"evidence_packet_row_count: {result['evidence_packet_row_count']}")
    print(f"strong_official_date_specific_count: {result['strong_official_date_specific_count']}")
    print(f"supporting_official_symbol_level_count: {result['supporting_official_symbol_level_count']}")
    print(f"supporting_local_eod_cache_count: {result['supporting_local_eod_cache_count']}")
    print(f"context_only_count: {result['context_only_count']}")
    print(f"missing_count: {result['missing_count']}")
    print(f"checklist_pass_count: {result['checklist_pass_count']}")
    print(f"blocked_count: {result['blocked_count']}")
    print(f"eod_low_budget_checklist_pass_count: {result['eod_low_budget_checklist_pass_count']}")
    print(f"report_path: {result['report_path']}")
    print(f"next_manual_action: {result['next_manual_action']}")
    print(
        "No approval applied, PIT review, export-readiness, staging, universe export, active mutation, "
        "data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked."
    )
    return 1 if result["status"] == "FAIL" else 0


def _handle_pit_official_status_evidence_packet_enrichment(args: argparse.Namespace) -> int:
    result = build_pit_official_status_evidence_packet_enrichment(
        packet=args.packet,
        quotation_probe=args.quotation_probe,
        policy_comparison=args.policy_comparison,
        output_dir=args.output_dir,
    )
    print(f"enrichment_id: {result.enrichment_id}")
    print(f"status: {result.status}")
    print(f"source_packet_id: {result.source_packet_id}")
    print(f"policy_comparison_id: {result.policy_comparison_id}")
    print(f"row_count: {result.row_count}")
    print(f"strong_official_date_specific_quotation_count: {result.strong_official_date_specific_quotation_count}")
    print(f"reviewed_no_hit_context_supported_count: {result.reviewed_no_hit_context_supported_count}")
    print(f"reviewer_acceptance_required_count: {result.reviewer_acceptance_required_count}")
    print(f"prior_official_symbol_level_context_count: {result.prior_official_symbol_level_context_count}")
    print(f"local_eod_cache_context_count: {result.local_eod_cache_context_count}")
    print(f"checklist_pass_count: {result.checklist_pass_count}")
    print(f"remaining_blocked_count: {result.remaining_blocked_count}")
    print(f"enriched_csv_path: {result.artifact_paths['enriched_csv']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print(
        "No approval applied, PIT review, export-readiness, staging, universe export, active mutation, "
        "data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked."
    )
    return 0


def _handle_pit_official_status_evidence_packet_enrichment_index(args: argparse.Namespace) -> int:
    result = build_pit_official_status_evidence_packet_enrichment_index(root=args.root, output_dir=args.output_dir)
    print(f"Index artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Index CSV path: {result['artifact_paths']['index_csv']}")
    print(f"artifact_count: {result['artifact_count']}")
    print("No approval, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 0


def _handle_pit_official_status_evidence_packet_enrichment_health(args: argparse.Namespace) -> int:
    result = check_pit_official_status_evidence_packet_enrichment_health(root=args.root, output_dir=args.output_dir)
    print(f"Health artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Health report path: {result['artifact_paths']['report']}")
    print(f"Health status: {result['status']}")
    print(f"checked_artifact_count: {result['checked_artifact_count']}")
    print(f"issue_count: {result['issue_count']}")
    print(f"error_count: {result['error_count']}")
    print(f"warning_count: {result['warning_count']}")
    print("No approval, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result["status"] == "FAIL" else 0


def _handle_pit_official_status_evidence_packet_enrichment_status(args: argparse.Namespace) -> int:
    result = run_pit_official_status_evidence_packet_enrichment_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Status report path: {result['artifact_paths']['report']}")
    print(f"status: {result['status']}")
    print(f"workflow_stage: {result['workflow_stage']}")
    print(f"latest_enrichment_id: {result['latest_enrichment_id']}")
    print(f"health_status: {result['health_status']}")
    print(f"source_packet_id: {result['source_packet_id']}")
    print(f"policy_comparison_id: {result['policy_comparison_id']}")
    print(f"row_count: {result['row_count']}")
    print(f"strong_official_date_specific_quotation_count: {result['strong_official_date_specific_quotation_count']}")
    print(f"reviewed_no_hit_context_supported_count: {result['reviewed_no_hit_context_supported_count']}")
    print(f"reviewer_acceptance_required_count: {result['reviewer_acceptance_required_count']}")
    print(f"checklist_pass_count: {result['checklist_pass_count']}")
    print(f"remaining_blocked_count: {result['remaining_blocked_count']}")
    print(f"report_path: {result['report_path']}")
    print(f"next_manual_action: {result['next_manual_action']}")
    print("No approval, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result["status"] == "FAIL" else 0


def _handle_reviewer_no_hit_source_coverage_acceptance(args: argparse.Namespace) -> int:
    result = build_reviewer_no_hit_source_coverage_acceptance(
        enrichment=args.enrichment,
        audit=args.audit,
        policy_comparison=args.policy_comparison,
        reviewer_acceptance=args.reviewer_acceptance,
        output_dir=args.output_dir,
    )
    print(f"acceptance_id: {result.acceptance_id}")
    print(f"status: {result.status}")
    print(f"enrichment_id: {result.enrichment_id}")
    print(f"source_packet_id: {result.source_packet_id}")
    print(f"policy_comparison_id: {result.policy_comparison_id}")
    print(f"row_count: {result.row_count}")
    print(f"accepted_count: {result.accepted_count}")
    print(f"needs_review_count: {result.needs_review_count}")
    print(f"needs_more_evidence_count: {result.needs_more_evidence_count}")
    print(f"reviewer_acceptance_required_count: {result.reviewer_acceptance_required_count}")
    print(f"accepted_supporting_context_count: {result.accepted_supporting_context_count}")
    print(f"survivorship_rationale_required_count: {result.survivorship_rationale_required_count}")
    print(f"checklist_pass_count: {result.checklist_pass_count}")
    print(f"remaining_blocked_count: {result.remaining_blocked_count}")
    print(f"acceptance_csv_path: {result.artifact_paths['acceptance_csv']}")
    print(f"template_csv_path: {result.artifact_paths['template_csv']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print("No approval, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 0


def _handle_reviewer_no_hit_source_coverage_acceptance_index(args: argparse.Namespace) -> int:
    result = build_reviewer_no_hit_source_coverage_acceptance_index(root=args.root, output_dir=args.output_dir)
    print(f"Index artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Index CSV path: {result['artifact_paths']['index_csv']}")
    print(f"artifact_count: {result['artifact_count']}")
    print("No approval, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 0


def _handle_reviewer_no_hit_source_coverage_acceptance_health(args: argparse.Namespace) -> int:
    result = check_reviewer_no_hit_source_coverage_acceptance_health(root=args.root, output_dir=args.output_dir)
    print(f"Health artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Health report path: {result['artifact_paths']['report']}")
    print(f"Health status: {result['status']}")
    print(f"checked_artifact_count: {result['checked_artifact_count']}")
    print(f"issue_count: {result['issue_count']}")
    print(f"error_count: {result['error_count']}")
    print(f"warning_count: {result['warning_count']}")
    print("No approval, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result["status"] == "FAIL" else 0


def _handle_reviewer_no_hit_source_coverage_acceptance_status(args: argparse.Namespace) -> int:
    result = run_reviewer_no_hit_source_coverage_acceptance_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Status report path: {result['artifact_paths']['report']}")
    print(f"status: {result['status']}")
    print(f"workflow_stage: {result['workflow_stage']}")
    print(f"latest_acceptance_id: {result['latest_acceptance_id']}")
    print(f"health_status: {result['health_status']}")
    print(f"enrichment_id: {result['enrichment_id']}")
    print(f"source_packet_id: {result['source_packet_id']}")
    print(f"policy_comparison_id: {result['policy_comparison_id']}")
    print(f"row_count: {result['row_count']}")
    print(f"accepted_count: {result['accepted_count']}")
    print(f"needs_review_count: {result['needs_review_count']}")
    print(f"needs_more_evidence_count: {result['needs_more_evidence_count']}")
    print(f"reviewer_acceptance_required_count: {result['reviewer_acceptance_required_count']}")
    print(f"accepted_supporting_context_count: {result['accepted_supporting_context_count']}")
    print(f"survivorship_rationale_required_count: {result['survivorship_rationale_required_count']}")
    print(f"checklist_pass_count: {result['checklist_pass_count']}")
    print(f"remaining_blocked_count: {result['remaining_blocked_count']}")
    print(f"report_path: {result['report_path']}")
    print(f"next_manual_action: {result['next_manual_action']}")
    print("No approval, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result["status"] == "FAIL" else 0


def _handle_reviewer_no_hit_acceptance_downstream_impact(args: argparse.Namespace) -> int:
    result = build_reviewer_no_hit_acceptance_downstream_impact(
        acceptance=args.acceptance,
        enrichment=args.enrichment,
        validator=args.validator,
        policy_comparison=args.policy_comparison,
        output_dir=args.output_dir,
    )
    print(f"impact_id: {result.impact_id}")
    print(f"status: {result.status}")
    print(f"acceptance_id: {result.acceptance_id}")
    print(f"enrichment_id: {result.enrichment_id}")
    print(f"source_packet_id: {result.source_packet_id}")
    print(f"reviewed_no_hit_policy_comparison_id: {result.reviewed_no_hit_policy_comparison_id}")
    print(f"validator_id: {result.validator_id}")
    print(f"row_count: {result.row_count}")
    print(f"accepted_no_hit_context_count: {result.accepted_no_hit_context_count}")
    print(f"packet_context_gap_reduced_count: {result.packet_context_gap_reduced_count}")
    print(f"checklist_pass_count: {result.checklist_pass_count}")
    print(f"remaining_blocked_count: {result.remaining_blocked_count}")
    print(f"impact_csv_path: {result.artifact_paths['impact_csv']}")
    print(f"packet_linkage_csv_path: {result.artifact_paths['packet_linkage_csv']}")
    print(f"checklist_policy_csv_path: {result.artifact_paths['checklist_policy_csv']}")
    print(f"remaining_blockers_csv_path: {result.artifact_paths['remaining_blockers_csv']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 0


def _handle_reviewer_no_hit_acceptance_downstream_impact_index(args: argparse.Namespace) -> int:
    result = build_reviewer_no_hit_acceptance_downstream_impact_index(root=args.root, output_dir=args.output_dir)
    print(f"Index artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Index CSV path: {result['artifact_paths']['index_csv']}")
    print(f"artifact_count: {result['artifact_count']}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 0


def _handle_reviewer_no_hit_acceptance_downstream_impact_health(args: argparse.Namespace) -> int:
    result = check_reviewer_no_hit_acceptance_downstream_impact_health(root=args.root, output_dir=args.output_dir)
    print(f"Health artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Health report path: {result['artifact_paths']['report']}")
    print(f"Health status: {result['status']}")
    print(f"checked_artifact_count: {result['checked_artifact_count']}")
    print(f"issue_count: {result['issue_count']}")
    print(f"error_count: {result['error_count']}")
    print(f"warning_count: {result['warning_count']}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result["status"] == "FAIL" else 0


def _handle_reviewer_no_hit_acceptance_downstream_impact_status(args: argparse.Namespace) -> int:
    result = run_reviewer_no_hit_acceptance_downstream_impact_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result['artifact_paths']['artifact_dir']}")
    print(f"Status report path: {result['artifact_paths']['report']}")
    print(f"status: {result['status']}")
    print(f"workflow_stage: {result['workflow_stage']}")
    print(f"latest_impact_id: {result['latest_impact_id']}")
    print(f"health_status: {result['health_status']}")
    print(f"acceptance_id: {result['acceptance_id']}")
    print(f"enrichment_id: {result['enrichment_id']}")
    print(f"source_packet_id: {result['source_packet_id']}")
    print(f"reviewed_no_hit_policy_comparison_id: {result['reviewed_no_hit_policy_comparison_id']}")
    print(f"validator_id: {result['validator_id']}")
    print(f"row_count: {result['row_count']}")
    print(f"accepted_no_hit_context_count: {result['accepted_no_hit_context_count']}")
    print(f"packet_context_gap_reduced_count: {result['packet_context_gap_reduced_count']}")
    print(f"checklist_pass_count: {result['checklist_pass_count']}")
    print(f"remaining_blocked_count: {result['remaining_blocked_count']}")
    print(f"approval_applied: {result['approval_applied']}")
    print(f"report_path: {result['report_path']}")
    print(f"next_manual_action: {result['next_manual_action']}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result["status"] == "FAIL" else 0


def _handle_first_batch_reviewer_evidence_completion_plan(args: argparse.Namespace) -> int:
    result = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=args.evidence_update_plan,
        downstream_impact=args.downstream_impact,
        enrichment=args.enrichment,
        validator=args.validator,
        policy_comparison=args.policy_comparison,
        output_dir=args.output_dir,
    )
    print(f"plan_id: {result.plan_id}")
    print(f"status: {result.status}")
    print(f"source_evidence_update_plan_id: {result.source_evidence_update_plan_id}")
    print(f"downstream_impact_id: {result.downstream_impact_id}")
    print(f"reviewer_no_hit_acceptance_id: {result.reviewer_no_hit_acceptance_id}")
    print(f"enrichment_id: {result.enrichment_id}")
    print(f"source_packet_id: {result.source_packet_id}")
    print(f"reviewed_no_hit_policy_comparison_id: {result.reviewed_no_hit_policy_comparison_id}")
    print(f"validator_id: {result.validator_id}")
    print(f"row_count: {result.row_count}")
    print(f"stock_core_row_count: {result.stock_core_row_count}")
    print(f"etf_core_row_count: {result.etf_core_row_count}")
    print(f"reviewer_completion_required_count: {result.reviewer_completion_required_count}")
    print(f"no_hit_acceptance_required_count: {result.no_hit_acceptance_required_count}")
    print(f"survivorship_rationale_required_count: {result.survivorship_rationale_required_count}")
    print(f"metadata_completion_required_count: {result.metadata_completion_required_count}")
    print(f"checklist_pass_count: {result.checklist_pass_count}")
    print(f"remaining_blocked_count: {result.remaining_blocked_count}")
    print(f"clean_review_updates_created: {result.clean_review_updates_created}")
    print(f"approval_applied: {result.approval_applied}")
    print(f"plan_csv_path: {result.artifact_paths['plan_csv']}")
    print(f"reviewer_completion_template_path: {result.artifact_paths['reviewer_completion_template']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 0


def _handle_first_batch_reviewer_evidence_completion_plan_index(args: argparse.Namespace) -> int:
    result = build_first_batch_reviewer_evidence_completion_plan_index(root=args.root, output_dir=args.output_dir)
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index CSV path: {result.artifact_paths['index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 0


def _handle_first_batch_reviewer_evidence_completion_plan_health(args: argparse.Namespace) -> int:
    result = check_first_batch_reviewer_evidence_completion_plan_health(root=args.root, output_dir=args.output_dir)
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Health report path: {result.artifact_paths['health_report']}")
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_first_batch_reviewer_evidence_completion_plan_status(args: argparse.Namespace) -> int:
    result = run_first_batch_reviewer_evidence_completion_plan_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Status report path: {result.artifact_paths['status_report']}")
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_plan_id: {result.latest_plan_id}")
    print(f"health_status: {result.health_status}")
    print(f"source_evidence_update_plan_id: {result.source_evidence_update_plan_id}")
    print(f"downstream_impact_id: {result.downstream_impact_id}")
    print(f"reviewer_no_hit_acceptance_id: {result.reviewer_no_hit_acceptance_id}")
    print(f"enrichment_id: {result.enrichment_id}")
    print(f"source_packet_id: {result.source_packet_id}")
    print(f"reviewed_no_hit_policy_comparison_id: {result.reviewed_no_hit_policy_comparison_id}")
    print(f"validator_id: {result.validator_id}")
    print(f"row_count: {result.row_count}")
    print(f"reviewer_completion_required_count: {result.reviewer_completion_required_count}")
    print(f"no_hit_acceptance_required_count: {result.no_hit_acceptance_required_count}")
    print(f"survivorship_rationale_required_count: {result.survivorship_rationale_required_count}")
    print(f"metadata_completion_required_count: {result.metadata_completion_required_count}")
    print(f"checklist_pass_count: {result.checklist_pass_count}")
    print(f"remaining_blocked_count: {result.remaining_blocked_count}")
    print(f"clean_review_updates_created: {result.clean_review_updates_created}")
    print(f"approval_applied: {result.approval_applied}")
    print(f"report_path: {result.report_path}")
    print(f"next_manual_action: {result.next_manual_action}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_first_batch_partial_completion_impact(args: argparse.Namespace) -> int:
    result = build_first_batch_partial_completion_impact(
        completion_plan=args.completion_plan,
        partial_completion=args.partial_completion,
        output_dir=args.output_dir,
    )
    print(f"impact_id: {result.impact_id}")
    print(f"status: {result.status}")
    print(f"completion_plan_id: {result.completion_plan_id}")
    print(f"partial_completion_path: {result.partial_completion_path}")
    print(f"row_count: {result.row_count}")
    print(f"completed_row_count: {result.completed_row_count}")
    print(f"completed_field_count: {result.completed_field_count}")
    print(f"blocker_reduced_count: {result.blocker_reduced_count}")
    print(f"material_blocker_reduced_count: {result.material_blocker_reduced_count}")
    print(f"checklist_pass_count: {result.checklist_pass_count}")
    print(f"remaining_blocked_count: {result.remaining_blocked_count}")
    print(f"clean_review_updates_created: {result.clean_review_updates_created}")
    print(f"approval_applied: {result.approval_applied}")
    print(f"impact_csv_path: {result.artifact_paths['impact_csv']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 0


def _handle_first_batch_partial_completion_impact_index(args: argparse.Namespace) -> int:
    result = build_first_batch_partial_completion_impact_index(root=args.root, output_dir=args.output_dir)
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index CSV path: {result.artifact_paths['index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 0


def _handle_first_batch_partial_completion_impact_health(args: argparse.Namespace) -> int:
    result = check_first_batch_partial_completion_impact_health(root=args.root, output_dir=args.output_dir)
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Health report path: {result.artifact_paths['health_report']}")
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_first_batch_partial_completion_impact_status(args: argparse.Namespace) -> int:
    result = run_first_batch_partial_completion_impact_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Status report path: {result.artifact_paths['status_report']}")
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_impact_id: {result.latest_impact_id}")
    print(f"health_status: {result.health_status}")
    print(f"completion_plan_id: {result.completion_plan_id}")
    print(f"row_count: {result.row_count}")
    print(f"completed_row_count: {result.completed_row_count}")
    print(f"completed_field_count: {result.completed_field_count}")
    print(f"blocker_reduced_count: {result.blocker_reduced_count}")
    print(f"material_blocker_reduced_count: {result.material_blocker_reduced_count}")
    print(f"checklist_pass_count: {result.checklist_pass_count}")
    print(f"remaining_blocked_count: {result.remaining_blocked_count}")
    print(f"clean_review_updates_created: {result.clean_review_updates_created}")
    print(f"approval_applied: {result.approval_applied}")
    print(f"report_path: {result.report_path}")
    print(f"next_manual_action: {result.next_manual_action}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_material_pit_evidence_gate_closure_plan(args: argparse.Namespace) -> int:
    result = build_material_pit_evidence_gate_closure_plan(
        audit=args.audit,
        partial_impact=args.partial_impact,
        completion_plan=args.completion_plan,
        validator=args.validator,
        policy_comparison=args.policy_comparison,
        enrichment=args.enrichment,
        reviewer_no_hit_acceptance=args.reviewer_no_hit_acceptance,
        reviewer_no_hit_downstream_impact=args.reviewer_no_hit_downstream_impact,
        output_dir=args.output_dir,
    )
    print(f"plan_id: {result.plan_id}")
    print(f"status: {result.status}")
    print(f"row_count: {result.row_count}")
    print(f"checklist_pass_candidate_count: {result.checklist_pass_candidate_count}")
    print(f"remaining_blocked_count: {result.remaining_blocked_count}")
    print(f"reusable_symbol_level_closure_count: {result.reusable_symbol_level_closure_count}")
    print(f"date_specific_closure_required_count: {result.date_specific_closure_required_count}")
    print(f"reviewer_no_hit_acceptance_required_count: {result.reviewer_no_hit_acceptance_required_count}")
    print(f"survivorship_rationale_required_count: {result.survivorship_rationale_required_count}")
    print(f"metadata_closure_required_count: {result.metadata_closure_required_count}")
    print(f"stock_st_no_st_required_count: {result.stock_st_no_st_required_count}")
    print(f"clean_review_updates_created: {result.clean_review_updates_created}")
    print(f"approval_applied: {result.approval_applied}")
    print(f"plan_csv_path: {result.artifact_paths['plan_csv']}")
    print(f"reviewer_fill_template_path: {result.artifact_paths['reviewer_fill_template_by_closure_path']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 0


def _handle_material_pit_evidence_gate_closure_plan_index(args: argparse.Namespace) -> int:
    result = build_material_pit_evidence_gate_closure_plan_index(root=args.root, output_dir=args.output_dir)
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index CSV path: {result.artifact_paths['index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 0


def _handle_material_pit_evidence_gate_closure_plan_health(args: argparse.Namespace) -> int:
    result = check_material_pit_evidence_gate_closure_plan_health(root=args.root, output_dir=args.output_dir)
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Health report path: {result.artifact_paths['health_report']}")
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_material_pit_evidence_gate_closure_plan_status(args: argparse.Namespace) -> int:
    result = run_material_pit_evidence_gate_closure_plan_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Status report path: {result.artifact_paths['status_report']}")
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_plan_id: {result.latest_plan_id}")
    print(f"health_status: {result.health_status}")
    print(f"row_count: {result.row_count}")
    print(f"checklist_pass_candidate_count: {result.checklist_pass_candidate_count}")
    print(f"remaining_blocked_count: {result.remaining_blocked_count}")
    print(f"reusable_symbol_level_closure_count: {result.reusable_symbol_level_closure_count}")
    print(f"date_specific_closure_required_count: {result.date_specific_closure_required_count}")
    print(f"reviewer_no_hit_acceptance_required_count: {result.reviewer_no_hit_acceptance_required_count}")
    print(f"survivorship_rationale_required_count: {result.survivorship_rationale_required_count}")
    print(f"metadata_closure_required_count: {result.metadata_closure_required_count}")
    print(f"stock_st_no_st_required_count: {result.stock_st_no_st_required_count}")
    print(f"clean_review_updates_created: {result.clean_review_updates_created}")
    print(f"approval_applied: {result.approval_applied}")
    print(f"report_path: {result.report_path}")
    print(f"next_manual_action: {result.next_manual_action}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_reviewer_material_evidence_fill_guidance(args: argparse.Namespace) -> int:
    result = build_reviewer_material_evidence_fill_guidance(
        material_plan=args.material_plan,
        audit=args.audit,
        completion_plan=args.completion_plan,
        partial_impact=args.partial_impact,
        validator=args.validator,
        enrichment=args.enrichment,
        reviewer_no_hit_acceptance=args.reviewer_no_hit_acceptance,
        reviewer_no_hit_downstream_impact=args.reviewer_no_hit_downstream_impact,
        output_dir=args.output_dir,
    )
    print(f"guidance_id: {result.guidance_id}")
    print(f"status: {result.status}")
    print(f"material_pit_evidence_gate_closure_plan_id: {result.material_pit_evidence_gate_closure_plan_id}")
    print(f"first_batch_partial_completion_impact_id: {result.first_batch_partial_completion_impact_id}")
    print(f"first_batch_reviewer_evidence_completion_plan_id: {result.first_batch_reviewer_evidence_completion_plan_id}")
    print(f"validator_id: {result.validator_id}")
    print(f"enrichment_id: {result.enrichment_id}")
    print(f"reviewer_no_hit_acceptance_id: {result.reviewer_no_hit_acceptance_id}")
    print(f"reviewer_no_hit_downstream_impact_id: {result.reviewer_no_hit_downstream_impact_id}")
    print(f"row_count: {result.row_count}")
    print(f"reviewer_guidance_row_count: {result.reviewer_guidance_row_count}")
    print(f"symbol_level_guidance_count: {result.symbol_level_guidance_count}")
    print(f"date_specific_guidance_count: {result.date_specific_guidance_count}")
    print(f"no_hit_acceptance_guidance_count: {result.no_hit_acceptance_guidance_count}")
    print(f"survivorship_rationale_guidance_count: {result.survivorship_rationale_guidance_count}")
    print(f"metadata_guidance_count: {result.metadata_guidance_count}")
    print(f"checklist_pass_candidate_count: {result.checklist_pass_candidate_count}")
    print(f"remaining_blocked_count: {result.remaining_blocked_count}")
    print(f"clean_review_updates_created: {result.clean_review_updates_created}")
    print(f"approval_applied: {result.approval_applied}")
    print(f"guidance_csv_path: {result.artifact_paths['guidance_csv']}")
    print(f"reviewer_fill_template_safe_defaults_path: {result.artifact_paths['reviewer_fill_template_safe_defaults']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 0


def _handle_reviewer_material_evidence_fill_guidance_index(args: argparse.Namespace) -> int:
    result = build_reviewer_material_evidence_fill_guidance_index(root=args.root, output_dir=args.output_dir)
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index CSV path: {result.artifact_paths['index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 0


def _handle_reviewer_material_evidence_fill_guidance_health(args: argparse.Namespace) -> int:
    result = check_reviewer_material_evidence_fill_guidance_health(root=args.root, output_dir=args.output_dir)
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Health report path: {result.artifact_paths['health_report']}")
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_reviewer_material_evidence_fill_guidance_status(args: argparse.Namespace) -> int:
    result = run_reviewer_material_evidence_fill_guidance_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Status report path: {result.artifact_paths['status_report']}")
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_guidance_id: {result.latest_guidance_id}")
    print(f"health_status: {result.health_status}")
    print(f"row_count: {result.row_count}")
    print(f"reviewer_guidance_row_count: {result.reviewer_guidance_row_count}")
    print(f"symbol_level_guidance_count: {result.symbol_level_guidance_count}")
    print(f"date_specific_guidance_count: {result.date_specific_guidance_count}")
    print(f"no_hit_acceptance_guidance_count: {result.no_hit_acceptance_guidance_count}")
    print(f"survivorship_rationale_guidance_count: {result.survivorship_rationale_guidance_count}")
    print(f"metadata_guidance_count: {result.metadata_guidance_count}")
    print(f"checklist_pass_candidate_count: {result.checklist_pass_candidate_count}")
    print(f"remaining_blocked_count: {result.remaining_blocked_count}")
    print(f"clean_review_updates_created: {result.clean_review_updates_created}")
    print(f"approval_applied: {result.approval_applied}")
    print(f"report_path: {result.report_path}")
    print(f"next_manual_action: {result.next_manual_action}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_one_row_material_evidence_fill_package(args: argparse.Namespace) -> int:
    result = build_one_row_material_evidence_fill_package(
        audit=args.audit,
        guidance=args.guidance,
        material_plan=args.material_plan,
        partial_impact=args.partial_impact,
        completion_plan=args.completion_plan,
        validator=args.validator,
        enrichment=args.enrichment,
        reviewer_no_hit_acceptance=args.reviewer_no_hit_acceptance,
        reviewer_no_hit_downstream_impact=args.reviewer_no_hit_downstream_impact,
        signal_date=args.signal_date,
        symbol=args.symbol,
        universe_name=args.universe_name,
        output_dir=args.output_dir,
    )
    print(f"package_id: {result.package_id}")
    print(f"status: {result.status}")
    print(f"reviewer_material_evidence_fill_guidance_id: {result.reviewer_material_evidence_fill_guidance_id}")
    print(f"material_pit_evidence_gate_closure_plan_id: {result.material_pit_evidence_gate_closure_plan_id}")
    print(f"first_batch_partial_completion_impact_id: {result.first_batch_partial_completion_impact_id}")
    print(f"first_batch_reviewer_evidence_completion_plan_id: {result.first_batch_reviewer_evidence_completion_plan_id}")
    print(f"validator_id: {result.validator_id}")
    print(f"enrichment_id: {result.enrichment_id}")
    print(f"reviewer_no_hit_acceptance_id: {result.reviewer_no_hit_acceptance_id}")
    print(f"reviewer_no_hit_downstream_impact_id: {result.reviewer_no_hit_downstream_impact_id}")
    print(f"signal_date: {result.request.signal_date}")
    print(f"symbol: {result.request.symbol}")
    print(f"universe_name: {result.request.universe_name}")
    print(f"package_row_count: {result.package_row_count}")
    print(f"context_field_drafted_count: {result.context_field_drafted_count}")
    print(f"material_blocker_closed_count: {result.material_blocker_closed_count}")
    print(f"checklist_pass_candidate_count: {result.checklist_pass_candidate_count}")
    print(f"remaining_blocked_count: {result.remaining_blocked_count}")
    print(f"clean_review_updates_created: {result.clean_review_updates_created}")
    print(f"approval_applied: {result.approval_applied}")
    print(f"package_csv_path: {result.artifact_paths['package_csv']}")
    print(f"drafted_context_fields_path: {result.artifact_paths['drafted_context_fields']}")
    print(f"remaining_blockers_after_fill_path: {result.artifact_paths['remaining_blockers_after_fill']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 0


def _handle_one_row_material_evidence_fill_package_index(args: argparse.Namespace) -> int:
    result = build_one_row_material_evidence_fill_package_index(root=args.root, output_dir=args.output_dir)
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index CSV path: {result.artifact_paths['index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 0


def _handle_one_row_material_evidence_fill_package_health(args: argparse.Namespace) -> int:
    result = check_one_row_material_evidence_fill_package_health(root=args.root, output_dir=args.output_dir)
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Health report path: {result.artifact_paths['health_report']}")
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_one_row_material_evidence_fill_package_status(args: argparse.Namespace) -> int:
    result = run_one_row_material_evidence_fill_package_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Status report path: {result.artifact_paths['status_report']}")
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_package_id: {result.latest_package_id}")
    print(f"health_status: {result.health_status}")
    print(f"target_signal_date: {result.target_signal_date}")
    print(f"target_symbol: {result.target_symbol}")
    print(f"target_universe_name: {result.target_universe_name}")
    print(f"package_row_count: {result.package_row_count}")
    print(f"context_field_drafted_count: {result.context_field_drafted_count}")
    print(f"material_blocker_closed_count: {result.material_blocker_closed_count}")
    print(f"checklist_pass_candidate_count: {result.checklist_pass_candidate_count}")
    print(f"remaining_blocked_count: {result.remaining_blocked_count}")
    print(f"clean_review_updates_created: {result.clean_review_updates_created}")
    print(f"approval_applied: {result.approval_applied}")
    print(f"report_path: {result.report_path}")
    print(f"next_manual_action: {result.next_manual_action}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_one_row_checklist_pass_candidate_preview(args: argparse.Namespace) -> int:
    result = build_one_row_checklist_pass_candidate_preview(
        audit=args.audit,
        package=args.package,
        guidance=args.guidance,
        material_plan=args.material_plan,
        completion_plan=args.completion_plan,
        validator=args.validator,
        enrichment=args.enrichment,
        reviewer_no_hit_acceptance=args.reviewer_no_hit_acceptance,
        reviewer_no_hit_downstream_impact=args.reviewer_no_hit_downstream_impact,
        signal_date=args.signal_date,
        symbol=args.symbol,
        universe_name=args.universe_name,
        output_dir=args.output_dir,
    )
    print(f"preview_id: {result.preview_id}")
    print(f"status: {result.status}")
    print(f"one_row_material_evidence_fill_package_id: {result.one_row_material_evidence_fill_package_id}")
    print(f"reviewer_material_evidence_fill_guidance_id: {result.reviewer_material_evidence_fill_guidance_id}")
    print(f"material_pit_evidence_gate_closure_plan_id: {result.material_pit_evidence_gate_closure_plan_id}")
    print(f"first_batch_reviewer_evidence_completion_plan_id: {result.first_batch_reviewer_evidence_completion_plan_id}")
    print(f"validator_id: {result.validator_id}")
    print(f"enrichment_id: {result.enrichment_id}")
    print(f"reviewer_no_hit_acceptance_id: {result.reviewer_no_hit_acceptance_id}")
    print(f"reviewer_no_hit_downstream_impact_id: {result.reviewer_no_hit_downstream_impact_id}")
    print(f"signal_date: {result.request.signal_date}")
    print(f"symbol: {result.request.symbol}")
    print(f"universe_name: {result.request.universe_name}")
    print(f"preview_row_count: {result.preview_row_count}")
    print(f"reusable_context_field_count: {result.reusable_context_field_count}")
    print(f"strict_requirement_gap_count: {result.strict_requirement_gap_count}")
    print(f"row_checklist_pass_candidate: {result.row_checklist_pass_candidate}")
    print(f"checklist_pass_candidate_count: {result.checklist_pass_candidate_count}")
    print(f"remaining_blocked_count: {result.remaining_blocked_count}")
    print(f"clean_review_updates_created: {result.clean_review_updates_created}")
    print(f"approval_applied: {result.approval_applied}")
    print(f"preview_csv_path: {result.artifact_paths['preview_csv']}")
    print(f"strict_requirement_gap_matrix_path: {result.artifact_paths['strict_requirement_gap_matrix']}")
    print(f"context_field_reuse_assessment_path: {result.artifact_paths['context_field_reuse_assessment']}")
    print(f"preview_safety_validation_path: {result.artifact_paths['preview_safety_validation']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 0


def _handle_one_row_checklist_pass_candidate_preview_index(args: argparse.Namespace) -> int:
    result = build_one_row_checklist_pass_candidate_preview_index(root=args.root, output_dir=args.output_dir)
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index CSV path: {result.artifact_paths['index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 0


def _handle_one_row_checklist_pass_candidate_preview_health(args: argparse.Namespace) -> int:
    result = check_one_row_checklist_pass_candidate_preview_health(root=args.root, output_dir=args.output_dir)
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Health report path: {result.artifact_paths['health_report']}")
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_one_row_checklist_pass_candidate_preview_status(args: argparse.Namespace) -> int:
    result = run_one_row_checklist_pass_candidate_preview_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Status report path: {result.artifact_paths['status_report']}")
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_preview_id: {result.latest_preview_id}")
    print(f"health_status: {result.health_status}")
    print(f"target_signal_date: {result.target_signal_date}")
    print(f"target_symbol: {result.target_symbol}")
    print(f"target_universe_name: {result.target_universe_name}")
    print(f"preview_row_count: {result.preview_row_count}")
    print(f"reusable_context_field_count: {result.reusable_context_field_count}")
    print(f"strict_requirement_gap_count: {result.strict_requirement_gap_count}")
    print(f"row_checklist_pass_candidate: {result.row_checklist_pass_candidate}")
    print(f"checklist_pass_candidate_count: {result.checklist_pass_candidate_count}")
    print(f"remaining_blocked_count: {result.remaining_blocked_count}")
    print(f"clean_review_updates_created: {result.clean_review_updates_created}")
    print(f"approval_applied: {result.approval_applied}")
    print(f"report_path: {result.report_path}")
    print(f"next_manual_action: {result.next_manual_action}")
    print("No approval, clean review updates, PIT review, export-readiness, staging, universe export, current-candidates generation, data writes, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_replay_substrate_schema_fixture(args: argparse.Namespace) -> int:
    result = build_replay_substrate_schema_fixture(output_dir=args.output_dir)
    print(f"fixture_id: {result.fixture_id}")
    print(f"status: {result.status}")
    print(f"entity_count: {result.entity_count}")
    print(f"validation_issue_count: {result.validation_issue_count}")
    print(f"overclaim_guard_count: {result.overclaim_guard_count}")
    print(f"overclaim_guard_pass_count: {result.overclaim_guard_pass_count}")
    print(f"report_only: {result.report_only}")
    print(f"diagnostic_only: {result.diagnostic_only}")
    print(f"forward_labels_computed: {result.forward_labels_computed}")
    print(f"weights_trained: {result.weights_trained}")
    print(f"active_stock_profile_created: {result.active_stock_profile_created}")
    print(f"real_buy_review_eligible: {result.real_buy_review_eligible}")
    print(f"artifact_dir: {result.artifact_paths['artifact_dir']}")
    print(f"entity_status_path: {result.artifact_paths['entity_status']}")
    print(f"validation_issues_path: {result.artifact_paths['validation_issues']}")
    print(f"overclaim_guards_path: {result.artifact_paths['overclaim_guards']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print("No replay, current-candidates, snapshot build, forward labels, weights training, active stock profile, data writes, API calls, messages, broker integration, orders, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_historical_replay_input_gate_validator(args: argparse.Namespace) -> int:
    result = run_historical_replay_input_gate_validator(
        input_package=args.input_package,
        output_dir=args.output_dir,
    )
    print(f"validator_run_id: {result.validator_run_id}")
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"gate_count: {result.gate_count}")
    print(f"passed_gate_count: {result.passed_gate_count}")
    print(f"blocked_gate_count: {result.blocked_gate_count}")
    print(f"blocker_count: {result.blocker_count}")
    print(f"pass_candidate: {result.pass_candidate}")
    print(f"active_replay_input_ready: {result.active_replay_input_ready}")
    print(f"active_replay_input: {result.active_replay_input}")
    print(f"forward_labels_exist: {result.forward_labels_exist}")
    print(f"weights_trained: {result.weights_trained}")
    print(f"active_stock_profile_exists: {result.active_stock_profile_exists}")
    print(f"real_buy_review_eligible: {result.real_buy_review_eligible}")
    print(f"report_path: {result.artifact_paths['input_gate_report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print(
        "No replay, current-candidates, snapshots, forward labels, training, active stock profiles, "
        "real buy-review eligibility, live trading, broker API, order placement, message delivery, "
        "LLM/API, external API, data/raw write, data/processed write, data/cache write, or cache mutation was invoked."
    )
    return 0


def _handle_historical_replay_input_gate_validator_index(args: argparse.Namespace) -> int:
    result = build_historical_replay_input_gate_validator_index(root=args.root, output_dir=args.output_dir)
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index CSV path: {result.artifact_paths['index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    print(
        "No replay, current-candidates, snapshots, forward labels, training, active stock profiles, "
        "research-status integration, data writes, API calls, messages, broker integration, orders, or cache mutation was invoked."
    )
    return 0


def _handle_historical_replay_input_gate_validator_health(args: argparse.Namespace) -> int:
    result = check_historical_replay_input_gate_validator_health(root=args.root, output_dir=args.output_dir)
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Health report path: {result.artifact_paths['health_report']}")
    print(f"status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(
        "No replay, current-candidates, snapshots, forward labels, training, active stock profiles, "
        "research-status integration, data writes, API calls, messages, broker integration, orders, or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_historical_replay_input_gate_validator_status(args: argparse.Namespace) -> int:
    result = run_historical_replay_input_gate_validator_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Status report path: {result.artifact_paths['status_report']}")
    print(f"status: {result.status}")
    print(f"health_status: {result.health_status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_validator_run_id: {result.latest_validator_run_id}")
    print(f"pass_candidate: {result.pass_candidate}")
    print(f"active_replay_input_ready: {result.active_replay_input_ready}")
    print(f"active_replay_input: {result.active_replay_input}")
    print(f"blocker_count: {result.blocker_count}")
    print(f"next_action: {result.next_action}")
    print(result.safety_statement)
    print(
        "No replay, current-candidates, snapshots, forward labels, training, active stock profiles, "
        "research-status integration, data writes, API calls, messages, broker integration, orders, or cache mutation was invoked."
    )
    return 0


def _handle_historical_replay_input_gate_validator_fixture(args: argparse.Namespace) -> int:
    result = build_historical_replay_input_gate_validator_fixture(output_dir=args.output_dir)
    print(f"fixture_run_id: {result.fixture_run_id}")
    print(f"status: {result.status}")
    print(f"case_count: {result.case_count}")
    print(f"blocked_case_count: {result.blocked_case_count}")
    print(f"pass_candidate_case_count: {result.pass_candidate_case_count}")
    print(f"active_ready_case_count: {result.active_ready_case_count}")
    print(f"validation_issue_count: {result.validation_issue_count}")
    print(f"overclaim_guard_pass_count: {result.overclaim_guard_pass_count}")
    print(f"overclaim_guard_total_count: {result.overclaim_guard_total_count}")
    print(f"active_replay_input: {result.active_replay_input}")
    print(f"forward_labels_exist: {result.forward_labels_exist}")
    print(f"weights_trained: {result.weights_trained}")
    print(f"active_stock_profile_exists: {result.active_stock_profile_exists}")
    print(f"real_buy_review_eligible: {result.real_buy_review_eligible}")
    print(f"report_only: {result.report_only}")
    print(f"diagnostic_only: {result.diagnostic_only}")
    print(f"validator_implemented: {result.validator_implemented}")
    print(f"artifact_dir: {result.artifact_paths['artifact_dir']}")
    print(f"fixture_cases_path: {result.artifact_paths['fixture_cases']}")
    print(f"blocked_requirements_path: {result.artifact_paths['blocked_requirements']}")
    print(f"expected_status_matrix_path: {result.artifact_paths['expected_status_matrix']}")
    print(f"overclaim_guard_report_path: {result.artifact_paths['overclaim_guard_report']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print("No replay, current-candidates, snapshot build, forward labels, weights training, active stock profile, real validator, index/health/status, research-status integration, checkpoint docs, data writes, API calls, messages, broker integration, orders, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_historical_replay_input_gate_validator_fixture_index(args: argparse.Namespace) -> int:
    result = build_historical_replay_input_gate_validator_fixture_index(
        root=args.root,
        output_dir=args.output_dir,
    )
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"artifact_count: {result.artifact_count}")
    print(f"index_csv: {result.artifact_paths['index_csv']}")
    print(f"index_report: {result.artifact_paths['index_report']}")
    print(f"metadata: {result.artifact_paths['metadata']}")
    if result.warnings:
        print("warnings:")
        for warning in result.warnings:
            print(f"- {warning}")
    print("No replay, current-candidates, snapshot build, forward labels, weights training, active stock profile, real validator, research-status integration, checkpoint docs, data writes, API calls, messages, broker integration, orders, or cache mutation was invoked.")
    return 0


def _handle_historical_replay_input_gate_validator_fixture_health(args: argparse.Namespace) -> int:
    result = check_historical_replay_input_gate_validator_fixture_health(
        root=args.root,
        output_dir=args.output_dir,
    )
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(f"health_csv: {result.artifact_paths['health_csv']}")
    print(f"health_report: {result.artifact_paths['health_report']}")
    print(f"metadata: {result.artifact_paths['metadata']}")
    print("No replay, current-candidates, snapshot build, forward labels, weights training, active stock profile, real validator, research-status integration, checkpoint docs, data writes, API calls, messages, broker integration, orders, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_historical_replay_input_gate_validator_fixture_status(args: argparse.Namespace) -> int:
    result = run_historical_replay_input_gate_validator_fixture_status(
        root=args.root,
        output_dir=args.output_dir,
    )
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"latest_fixture_run_id: {result.latest_fixture_run_id}")
    print(f"status: {result.status}")
    print(f"health_status: {result.health_status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"case_count: {result.case_count}")
    print(f"blocked_case_count: {result.blocked_case_count}")
    print(f"pass_candidate_case_count: {result.pass_candidate_case_count}")
    print(f"active_ready_case_count: {result.active_ready_case_count}")
    print(f"active_replay_input: {result.active_replay_input}")
    print(f"forward_labels_exist: {result.forward_labels_exist}")
    print(f"weights_trained: {result.weights_trained}")
    print(f"active_stock_profile_exists: {result.active_stock_profile_exists}")
    print(f"real_buy_review_eligible: {result.real_buy_review_eligible}")
    print(f"validator_implemented: {result.validator_implemented}")
    print(f"safety_statement: {result.safety_statement}")
    print(f"status_csv: {result.artifact_paths['status_csv']}")
    print(f"status_report: {result.artifact_paths['status_report']}")
    print(f"metadata: {result.artifact_paths['metadata']}")
    print("No replay, current-candidates, snapshot build, forward labels, weights training, active stock profile, real validator, research-status integration, checkpoint docs, data writes, API calls, messages, broker integration, orders, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_replay_substrate_schema_fixture_index(args: argparse.Namespace) -> int:
    result = build_replay_substrate_schema_fixture_index(root=args.root, output_dir=args.output_dir)
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index CSV path: {result.artifact_paths['index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    print("No replay, current-candidates, snapshot build, forward labels, weights training, active stock profile, data writes, API calls, messages, broker integration, orders, or cache mutation was invoked.")
    return 0


def _handle_replay_substrate_schema_fixture_health(args: argparse.Namespace) -> int:
    result = check_replay_substrate_schema_fixture_health(root=args.root, output_dir=args.output_dir)
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Health report path: {result.artifact_paths['health_report']}")
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print("No replay, current-candidates, snapshot build, forward labels, weights training, active stock profile, data writes, API calls, messages, broker integration, orders, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_replay_substrate_schema_fixture_status(args: argparse.Namespace) -> int:
    result = run_replay_substrate_schema_fixture_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Status report path: {result.artifact_paths['status_report']}")
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_fixture_id: {result.latest_fixture_id}")
    print(f"health_status: {result.health_status}")
    print(f"entity_count: {result.entity_count}")
    print(f"validation_issue_count: {result.validation_issue_count}")
    print(f"overclaim_guard_status: {result.overclaim_guard_status}")
    print(f"overclaim_guard_pass_count: {result.overclaim_guard_pass_count}")
    print(f"overclaim_guard_total_count: {result.overclaim_guard_total_count}")
    print(f"active_replay_input: {result.active_replay_input}")
    print(f"forward_labels_exist: {result.forward_labels_exist}")
    print(f"weights_trained: {result.weights_trained}")
    print(f"active_stock_profile_exists: {result.active_stock_profile_exists}")
    print(f"real_buy_review_eligible: {result.real_buy_review_eligible}")
    print(f"report_only: {result.report_only}")
    print(f"diagnostic_only: {result.diagnostic_only}")
    print(f"no_live_trading: {result.no_live_trading}")
    print(f"no_broker_api: {result.no_broker_api}")
    print(f"no_order_placement: {result.no_order_placement}")
    print(f"report_path: {result.report_path}")
    print(f"next_manual_action: {result.next_manual_action}")
    print("This is a report-only replay substrate schema fixture. It is not real replay, forward-label computation, training, stock-profile validation, or real buy-review eligibility.")
    print("No replay, current-candidates, snapshot build, forward labels, weights training, active stock profile, data writes, API calls, messages, broker integration, orders, or cache mutation was invoked.")
    return 1 if result.status == "FAIL" else 0


def _handle_universe_profile_policy_audit(args: argparse.Namespace) -> int:
    result = build_universe_profile_policy_audit(
        worklist=args.worklist,
        review=args.review,
        output_dir=args.output_dir,
    )
    print(f"audit_id: {result.audit_id}")
    print(f"status: {result.status}")
    print(f"row_count: {result.row_count}")
    print(f"universe_count: {result.universe_count}")
    print(f"mixed_universe_count: {result.mixed_universe_count}")
    print(f"ambiguous_policy_count: {result.ambiguous_policy_count}")
    print(f"stock_row_count: {result.stock_row_count}")
    print(f"etf_row_count: {result.etf_row_count}")
    print(f"recommended_stock_core_count: {result.recommended_stock_core_count}")
    print(f"recommended_etf_core_count: {result.recommended_etf_core_count}")
    print(f"recommended_mixed_demo_core_count: {result.recommended_mixed_demo_core_count}")
    print(f"audit_csv_path: {result.artifact_paths['audit_csv']}")
    print(f"summary_csv_path: {result.artifact_paths['summary_csv']}")
    print(f"split_guidance_csv_path: {result.artifact_paths['split_guidance_csv']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, rejection, universe export, data/raw write, data/processed write, "
        "current-candidates generation, snapshot build, forward labels, live trading, broker API, "
        "order placement, message delivery, network/API, LLM/API, or cache mutation was invoked."
    )
    return 0


def _handle_universe_profile_policy_audit_index(args: argparse.Namespace) -> int:
    result = build_universe_profile_policy_audit_index(
        root=args.root,
        output_dir=args.output_dir,
        include_missing_metadata=bool(args.include_missing_metadata),
    )
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Index CSV path: "
        f"{result.artifact_paths['universe_profile_policy_audit_index_csv']}"
    )
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, rejection, universe export, data/raw write, data/processed write, "
        "current-candidates generation, snapshot build, forward labels, live trading, broker API, "
        "order placement, message delivery, network/API, LLM/API, or cache mutation was invoked."
    )
    return 0


def _handle_universe_profile_policy_audit_health(args: argparse.Namespace) -> int:
    result = check_universe_profile_policy_audit_health(
        index_path=args.index,
        root=args.root,
        output_dir=args.output_dir,
    )
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Health report path: "
        f"{result.artifact_paths['universe_profile_policy_audit_health_report']}"
    )
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(
        "No approval, rejection, universe export, data/raw write, data/processed write, "
        "current-candidates generation, snapshot build, forward labels, live trading, broker API, "
        "order placement, message delivery, network/API, LLM/API, or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_universe_profile_policy_audit_status(args: argparse.Namespace) -> int:
    result = run_universe_profile_policy_audit_status(root=args.root, output_dir=args.output_dir)
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Status report path: "
        f"{result.artifact_paths['universe_profile_policy_audit_status_report']}"
    )
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_audit_id: {result.latest_audit_id}")
    print(f"health_status: {result.health_status}")
    print(f"row_count: {result.row_count}")
    print(f"stock_row_count: {result.stock_row_count}")
    print(f"etf_row_count: {result.etf_row_count}")
    print(f"mixed_universe_count: {result.mixed_universe_count}")
    print(f"ambiguous_policy_count: {result.ambiguous_policy_count}")
    print(f"recommended_stock_core_count: {result.recommended_stock_core_count}")
    print(f"recommended_etf_core_count: {result.recommended_etf_core_count}")
    print(f"recommended_mixed_demo_core_count: {result.recommended_mixed_demo_core_count}")
    print(f"report_path: {summary.get('report_path', '')}")
    print(f"next_manual_action: {result.next_manual_action}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, rejection, universe export, data/raw write, data/processed write, "
        "current-candidates generation, snapshot build, forward labels, live trading, broker API, "
        "order placement, message delivery, network/API, LLM/API, or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_universe_profile_split_worklist_plan(args: argparse.Namespace) -> int:
    result = build_universe_profile_split_worklist_plan(
        worklist=args.worklist,
        policy_audit=args.policy_audit,
        profiles=args.profiles,
        output_dir=args.output_dir,
    )
    print(f"plan_id: {result.plan_id}")
    print(f"status: {result.status}")
    print(f"row_count: {result.row_count}")
    print(f"stock_row_count: {result.stock_row_count}")
    print(f"etf_row_count: {result.etf_row_count}")
    print(f"unknown_instrument_type_count: {result.unknown_instrument_type_count}")
    print(f"legacy_mixed_demo_row_count: {result.legacy_mixed_demo_row_count}")
    print(f"recommended_stock_core_count: {result.recommended_stock_core_count}")
    print(f"recommended_etf_core_count: {result.recommended_etf_core_count}")
    print(f"recommended_mixed_demo_core_count: {result.recommended_mixed_demo_core_count}")
    print(f"profile_conflict_count: {result.profile_conflict_count}")
    print("active_worklist_mutated: False")
    print(f"registry_snapshot_path: {result.artifact_paths['registry_snapshot']}")
    print(f"plan_csv_path: {result.artifact_paths['plan_csv']}")
    print(f"summary_csv_path: {result.artifact_paths['summary_csv']}")
    print(f"stock_core_guidance_path: {result.artifact_paths['stock_core_guidance']}")
    print(f"etf_core_guidance_path: {result.artifact_paths['etf_core_guidance']}")
    print(f"mixed_demo_core_guidance_path: {result.artifact_paths['mixed_demo_core_guidance']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 0


def _handle_universe_profile_split_worklist_plan_index(args: argparse.Namespace) -> int:
    result = build_universe_profile_split_worklist_plan_index(
        root=args.root,
        output_dir=args.output_dir,
        include_missing_metadata=bool(args.include_missing_metadata),
    )
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Index CSV path: "
        f"{result.artifact_paths['universe_profile_split_worklist_plan_index_csv']}"
    )
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 0


def _handle_universe_profile_split_worklist_plan_health(args: argparse.Namespace) -> int:
    result = check_universe_profile_split_worklist_plan_health(
        index_path=args.index,
        root=args.root,
        output_dir=args.output_dir,
    )
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Health report path: "
        f"{result.artifact_paths['universe_profile_split_worklist_plan_health_report']}"
    )
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_universe_profile_split_worklist_plan_status(args: argparse.Namespace) -> int:
    result = run_universe_profile_split_worklist_plan_status(root=args.root, output_dir=args.output_dir)
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Status report path: "
        f"{result.artifact_paths['universe_profile_split_worklist_plan_status_report']}"
    )
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_plan_id: {result.latest_plan_id}")
    print(f"health_status: {result.health_status}")
    print(f"row_count: {result.row_count}")
    print(f"stock_row_count: {result.stock_row_count}")
    print(f"etf_row_count: {result.etf_row_count}")
    print(f"legacy_mixed_demo_row_count: {result.legacy_mixed_demo_row_count}")
    print(f"recommended_stock_core_count: {result.recommended_stock_core_count}")
    print(f"recommended_etf_core_count: {result.recommended_etf_core_count}")
    print(f"recommended_mixed_demo_core_count: {result.recommended_mixed_demo_core_count}")
    print(f"profile_conflict_count: {result.profile_conflict_count}")
    print(f"report_path: {summary.get('report_path', '')}")
    print(f"next_manual_action: {result.next_manual_action}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_reviewed_replacement_worklist_plan(args: argparse.Namespace) -> int:
    result = build_reviewed_replacement_worklist_plan(
        split_plan=args.split_plan,
        output_dir=args.output_dir,
    )
    print(f"replacement_plan_id: {result.replacement_plan_id}")
    print(f"status: {result.status}")
    print(f"row_count: {result.row_count}")
    print(f"stock_core_row_count: {result.stock_core_row_count}")
    print(f"etf_core_row_count: {result.etf_core_row_count}")
    print(f"mixed_demo_core_row_count: {result.mixed_demo_core_row_count}")
    print(f"profile_conflict_count: {result.profile_conflict_count}")
    print(f"active_worklist_mutated: {result.active_worklist_mutated}")
    print(f"plan_csv_path: {result.artifact_paths['reviewed_replacement_worklist_plan']}")
    print(f"replacement_worklist_stock_core_path: {result.artifact_paths['replacement_worklist_stock_core']}")
    print(f"replacement_worklist_etf_core_path: {result.artifact_paths['replacement_worklist_etf_core']}")
    print(f"replacement_worklist_mixed_demo_core_path: {result.artifact_paths['replacement_worklist_mixed_demo_core']}")
    print(f"replacement_update_template_stock_core_path: {result.artifact_paths['replacement_update_template_stock_core']}")
    print(f"replacement_update_template_etf_core_path: {result.artifact_paths['replacement_update_template_etf_core']}")
    print(
        "replacement_update_template_mixed_demo_core_path: "
        f"{result.artifact_paths['replacement_update_template_mixed_demo_core']}"
    )
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 0


def _handle_reviewed_replacement_worklist_plan_index(args: argparse.Namespace) -> int:
    result = build_reviewed_replacement_worklist_plan_index(
        root=args.root,
        output_dir=args.output_dir,
        include_missing_metadata=bool(args.include_missing_metadata),
    )
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index CSV path: {result.artifact_paths['reviewed_replacement_worklist_plan_index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 0


def _handle_reviewed_replacement_worklist_plan_health(args: argparse.Namespace) -> int:
    result = check_reviewed_replacement_worklist_plan_health(
        root=args.root,
        index_path=args.index,
        output_dir=args.output_dir,
    )
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Health report path: {result.artifact_paths['reviewed_replacement_worklist_plan_health_report']}")
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_reviewed_replacement_worklist_plan_status(args: argparse.Namespace) -> int:
    result = run_reviewed_replacement_worklist_plan_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Status report path: {result.artifact_paths['reviewed_replacement_worklist_plan_status_report']}")
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_replacement_plan_id: {result.latest_replacement_plan_id}")
    print(f"health_status: {result.health_status}")
    print(f"source_split_plan_id: {result.source_split_plan_id}")
    print(f"row_count: {result.row_count}")
    print(f"stock_core_row_count: {result.stock_core_row_count}")
    print(f"etf_core_row_count: {result.etf_core_row_count}")
    print(f"mixed_demo_core_row_count: {result.mixed_demo_core_row_count}")
    print(f"profile_conflict_count: {result.profile_conflict_count}")
    print(f"active_worklist_mutated: {result.active_worklist_mutated}")
    print(f"report_path: {result.report_path}")
    print(f"next_manual_action: {result.next_manual_action}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_reviewed_replacement_worklist_acceptance(args: argparse.Namespace) -> int:
    result = build_reviewed_replacement_worklist_acceptance(
        replacement_plan=args.replacement_plan,
        accepted_by=args.accepted_by,
        accepted_at=args.accepted_at,
        acceptance_reason=args.acceptance_reason,
        manual_acceptance=bool(args.manual_acceptance),
        output_dir=args.output_dir,
    )
    print(f"acceptance_id: {result.acceptance_id}")
    print(f"status: {result.status}")
    print(f"replacement_plan_id: {result.replacement_plan_id}")
    print(f"source_split_plan_id: {result.source_split_plan_id}")
    print(f"source_policy_audit_id: {result.source_policy_audit_id}")
    print(f"source_worklist_id: {result.source_worklist_id}")
    print(f"row_count: {result.row_count}")
    print(f"stock_core_row_count: {result.stock_core_row_count}")
    print(f"etf_core_row_count: {result.etf_core_row_count}")
    print(f"mixed_demo_core_row_count: {result.mixed_demo_core_row_count}")
    print(f"profile_conflict_count: {result.profile_conflict_count}")
    print(f"acceptance_acknowledged: {result.acceptance_acknowledged}")
    print(f"active_worklist_mutated: {result.active_worklist_mutated}")
    print(f"acceptance_csv_path: {result.artifact_paths['reviewed_replacement_worklist_acceptance']}")
    print(f"accepted_replacement_worklist_stock_core_path: {result.artifact_paths['accepted_replacement_worklist_stock_core']}")
    print(f"accepted_replacement_worklist_etf_core_path: {result.artifact_paths['accepted_replacement_worklist_etf_core']}")
    print(
        "accepted_replacement_worklist_mixed_demo_core_path: "
        f"{result.artifact_paths['accepted_replacement_worklist_mixed_demo_core']}"
    )
    print(f"accepted_update_template_stock_core_path: {result.artifact_paths['accepted_update_template_stock_core']}")
    print(f"accepted_update_template_etf_core_path: {result.artifact_paths['accepted_update_template_etf_core']}")
    print(
        "accepted_update_template_mixed_demo_core_path: "
        f"{result.artifact_paths['accepted_update_template_mixed_demo_core']}"
    )
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 0


def _handle_reviewed_replacement_worklist_acceptance_index(args: argparse.Namespace) -> int:
    result = build_reviewed_replacement_worklist_acceptance_index(
        root=args.root,
        output_dir=args.output_dir,
        include_missing_metadata=bool(args.include_missing_metadata),
    )
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index CSV path: {result.artifact_paths['reviewed_replacement_worklist_acceptance_index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 0


def _handle_reviewed_replacement_worklist_acceptance_health(args: argparse.Namespace) -> int:
    result = check_reviewed_replacement_worklist_acceptance_health(
        root=args.root,
        index_path=args.index,
        output_dir=args.output_dir,
    )
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Health report path: {result.artifact_paths['reviewed_replacement_worklist_acceptance_health_report']}")
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_reviewed_replacement_worklist_acceptance_status(args: argparse.Namespace) -> int:
    result = run_reviewed_replacement_worklist_acceptance_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Status report path: {result.artifact_paths['reviewed_replacement_worklist_acceptance_status_report']}")
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_acceptance_id: {result.latest_acceptance_id}")
    print(f"health_status: {result.health_status}")
    print(f"replacement_plan_id: {result.replacement_plan_id}")
    print(f"source_split_plan_id: {result.source_split_plan_id}")
    print(f"source_policy_audit_id: {result.source_policy_audit_id}")
    print(f"source_worklist_id: {result.source_worklist_id}")
    print(f"row_count: {result.row_count}")
    print(f"stock_core_row_count: {result.stock_core_row_count}")
    print(f"etf_core_row_count: {result.etf_core_row_count}")
    print(f"mixed_demo_core_row_count: {result.mixed_demo_core_row_count}")
    print(f"profile_conflict_count: {result.profile_conflict_count}")
    print(f"acceptance_acknowledged: {result.acceptance_acknowledged}")
    print(f"active_worklist_mutated: {result.active_worklist_mutated}")
    print(f"report_path: {result.report_path}")
    print(f"next_manual_action: {result.next_manual_action}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_reviewed_replacement_worklist_activation(args: argparse.Namespace) -> int:
    result = build_reviewed_replacement_worklist_activation(
        acceptance=args.acceptance,
        activated_by=args.activated_by,
        activated_at=args.activated_at,
        activation_reason=args.activation_reason,
        manual_activation=bool(args.manual_activation),
        output_dir=args.output_dir,
    )
    print(f"activation_id: {result.activation_id}")
    print(f"status: {result.status}")
    print(f"replacement_plan_id: {result.replacement_plan_id}")
    print(f"source_split_plan_id: {result.source_split_plan_id}")
    print(f"source_policy_audit_id: {result.source_policy_audit_id}")
    print(f"source_worklist_id: {result.source_worklist_id}")
    print(f"row_count: {result.row_count}")
    print(f"stock_core_row_count: {result.stock_core_row_count}")
    print(f"etf_core_row_count: {result.etf_core_row_count}")
    print(f"mixed_demo_core_row_count: {result.mixed_demo_core_row_count}")
    print(f"profile_conflict_count: {result.profile_conflict_count}")
    print(f"activation_acknowledged: {result.activation_acknowledged}")
    print(f"active_worklist_mutated: {result.active_worklist_mutated}")
    print(f"activation_csv_path: {result.artifact_paths['reviewed_replacement_worklist_activation']}")
    print(f"activated_replacement_worklist_stock_core_path: {result.artifact_paths['activated_replacement_worklist_stock_core']}")
    print(f"activated_replacement_worklist_etf_core_path: {result.artifact_paths['activated_replacement_worklist_etf_core']}")
    print(
        "activated_replacement_worklist_mixed_demo_core_path: "
        f"{result.artifact_paths['activated_replacement_worklist_mixed_demo_core']}"
    )
    print(f"activated_update_template_stock_core_path: {result.artifact_paths['activated_update_template_stock_core']}")
    print(f"activated_update_template_etf_core_path: {result.artifact_paths['activated_update_template_etf_core']}")
    print(
        "activated_update_template_mixed_demo_core_path: "
        f"{result.artifact_paths['activated_update_template_mixed_demo_core']}"
    )
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 0


def _handle_reviewed_replacement_worklist_activation_index(args: argparse.Namespace) -> int:
    result = build_reviewed_replacement_worklist_activation_index(
        root=args.root,
        output_dir=args.output_dir,
        include_missing_metadata=bool(args.include_missing_metadata),
    )
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index CSV path: {result.artifact_paths['reviewed_replacement_worklist_activation_index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 0


def _handle_reviewed_replacement_worklist_activation_health(args: argparse.Namespace) -> int:
    result = check_reviewed_replacement_worklist_activation_health(
        root=args.root,
        index_path=args.index,
        output_dir=args.output_dir,
    )
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Health report path: {result.artifact_paths['reviewed_replacement_worklist_activation_health_report']}")
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_reviewed_replacement_worklist_activation_status(args: argparse.Namespace) -> int:
    result = run_reviewed_replacement_worklist_activation_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Status report path: {result.artifact_paths['reviewed_replacement_worklist_activation_status_report']}")
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_activation_id: {result.latest_activation_id}")
    print(f"health_status: {result.health_status}")
    print(f"replacement_plan_id: {result.replacement_plan_id}")
    print(f"source_split_plan_id: {result.source_split_plan_id}")
    print(f"source_policy_audit_id: {result.source_policy_audit_id}")
    print(f"source_worklist_id: {result.source_worklist_id}")
    print(f"row_count: {result.row_count}")
    print(f"stock_core_row_count: {result.stock_core_row_count}")
    print(f"etf_core_row_count: {result.etf_core_row_count}")
    print(f"mixed_demo_core_row_count: {result.mixed_demo_core_row_count}")
    print(f"profile_conflict_count: {result.profile_conflict_count}")
    print(f"activation_acknowledged: {result.activation_acknowledged}")
    print(f"active_worklist_mutated: {result.active_worklist_mutated}")
    print(f"report_path: {result.report_path}")
    print(f"next_manual_action: {result.next_manual_action}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_activated_replacement_worklist_evidence_update_plan(args: argparse.Namespace) -> int:
    result = build_activated_replacement_worklist_evidence_update_plan(
        activation=args.activation,
        output_dir=args.output_dir,
    )
    print(f"plan_id: {result.plan_id}")
    print(f"status: {result.status}")
    print(f"activation_id: {result.activation_id}")
    print(f"acceptance_id: {result.acceptance_id}")
    print(f"replacement_plan_id: {result.replacement_plan_id}")
    print(f"source_split_plan_id: {result.source_split_plan_id}")
    print(f"source_policy_audit_id: {result.source_policy_audit_id}")
    print(f"source_worklist_id: {result.source_worklist_id}")
    print(f"row_count: {result.row_count}")
    print(f"stock_core_row_count: {result.stock_core_row_count}")
    print(f"etf_core_row_count: {result.etf_core_row_count}")
    print(f"mixed_demo_core_row_count: {result.mixed_demo_core_row_count}")
    print(f"stock_core_first_batch_row_count: {result.stock_core_first_batch_row_count}")
    print(f"etf_core_first_batch_row_count: {result.etf_core_first_batch_row_count}")
    print(f"approved_count: {result.approved_count}")
    print(f"rejected_count: {result.rejected_count}")
    print(f"valid_for_signal_date_count: {result.valid_for_signal_date_count}")
    print(f"clean_review_updates_created: {result.clean_review_updates_created}")
    print(f"plan_csv_path: {result.artifact_paths['plan_csv']}")
    print(f"stock_core_update_template_path: {result.artifact_paths['stock_core_update_template']}")
    print(f"etf_core_update_template_path: {result.artifact_paths['etf_core_update_template']}")
    print(f"stock_core_first_batch_package_path: {result.artifact_paths['stock_core_first_batch_package']}")
    print(f"etf_core_first_batch_package_path: {result.artifact_paths['etf_core_first_batch_package']}")
    print(f"evidence_source_checklist_path: {result.artifact_paths['evidence_source_checklist']}")
    print(f"report_path: {result.artifact_paths['report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 0


def _handle_activated_replacement_worklist_evidence_update_plan_index(args: argparse.Namespace) -> int:
    result = build_activated_replacement_worklist_evidence_update_plan_index(
        root=args.root,
        output_dir=args.output_dir,
    )
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index CSV path: {result.artifact_paths['index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 0


def _handle_activated_replacement_worklist_evidence_update_plan_health(args: argparse.Namespace) -> int:
    result = check_activated_replacement_worklist_evidence_update_plan_health(
        root=args.root,
        output_dir=args.output_dir,
    )
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Health report path: {result.artifact_paths['health_report']}")
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_activated_replacement_worklist_evidence_update_plan_status(args: argparse.Namespace) -> int:
    result = run_activated_replacement_worklist_evidence_update_plan_status(root=args.root, output_dir=args.output_dir)
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Status report path: {result.artifact_paths['status_report']}")
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_plan_id: {result.latest_plan_id}")
    print(f"health_status: {result.health_status}")
    print(f"activation_id: {result.activation_id}")
    print(f"acceptance_id: {result.acceptance_id}")
    print(f"replacement_plan_id: {result.replacement_plan_id}")
    print(f"source_split_plan_id: {result.source_split_plan_id}")
    print(f"source_policy_audit_id: {result.source_policy_audit_id}")
    print(f"source_worklist_id: {result.source_worklist_id}")
    print(f"row_count: {result.row_count}")
    print(f"stock_core_row_count: {result.stock_core_row_count}")
    print(f"etf_core_row_count: {result.etf_core_row_count}")
    print(f"mixed_demo_core_row_count: {result.mixed_demo_core_row_count}")
    print(f"approved_count: {result.approved_count}")
    print(f"valid_for_signal_date_count: {result.valid_for_signal_date_count}")
    print(f"clean_review_updates_created: {result.clean_review_updates_created}")
    print(f"report_path: {result.report_path}")
    print(f"next_manual_action: {result.next_manual_action}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No approval, rejection, active worklist mutation, universe export, data/raw write, "
        "data/processed write, current-candidates generation, snapshot build, forward labels, "
        "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
        "or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_pit_universe_evidence_completion_helper_index(args: argparse.Namespace) -> int:
    result = build_pit_universe_evidence_completion_helper_index(
        root=args.root,
        output_dir=args.output_dir,
        include_missing_metadata=bool(args.include_missing_metadata),
    )
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Index CSV path: "
        f"{result.artifact_paths['pit_universe_evidence_completion_helper_index_csv']}"
    )
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, "
        "LLM/API, external API, or cache mutation was invoked."
    )
    return 0


def _handle_pit_universe_evidence_completion_helper_health(args: argparse.Namespace) -> int:
    result = check_pit_universe_evidence_completion_helper_health(
        index_path=args.index,
        root=args.root,
        output_dir=args.output_dir,
    )
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Health report path: "
        f"{result.artifact_paths['pit_universe_evidence_completion_helper_health_report']}"
    )
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, "
        "LLM/API, external API, or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_pit_universe_evidence_completion_helper_status(args: argparse.Namespace) -> int:
    result = run_pit_universe_evidence_completion_helper_status(root=args.root, output_dir=args.output_dir)
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Status report path: "
        f"{result.artifact_paths['pit_universe_evidence_completion_helper_status_report']}"
    )
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_helper_id: {result.latest_helper_id}")
    print(f"health_status: {result.health_status}")
    print(f"review_id: {result.review_id}")
    print(f"row_count: {result.row_count}")
    print(f"needs_evidence_count: {result.needs_evidence_count}")
    print(f"rows_with_base_hints_count: {result.rows_with_base_hints_count}")
    print(f"future_dated_hint_count: {result.future_dated_hint_count}")
    print(f"authoritative_hint_count: {result.authoritative_hint_count}")
    print(f"report_path: {summary.get('report_path', '')}")
    print(f"next_manual_action: {result.next_manual_action}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, "
        "LLM/API, external API, or cache mutation was invoked."
    )
    return 1 if result.status == "FAIL" else 0


def _handle_current_candidates_backfill_execution_manifest_index(args: argparse.Namespace) -> int:
    result = build_current_candidates_backfill_execution_manifest_index(
        root=args.root,
        output_dir=args.output_dir,
        include_missing_metadata=bool(args.include_missing_metadata),
    )
    print(f"Index artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Index CSV path: "
        f"{result.artifact_paths['current_candidates_backfill_execution_manifest_index_csv']}"
    )
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
        "order placement, message delivery, or network/API call was invoked."
    )
    return 0


def _handle_current_candidates_backfill_execution_manifest_health(args: argparse.Namespace) -> int:
    result = check_current_candidates_backfill_execution_manifest_health(
        index_path=args.index,
        root=args.root,
        output_dir=args.output_dir,
    )
    print(f"Health artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Health report path: "
        f"{result.artifact_paths['current_candidates_backfill_execution_manifest_health_report']}"
    )
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
        "order placement, message delivery, or network/API call was invoked."
    )
    return 0


def _handle_current_candidates_backfill_execution_manifest_status(args: argparse.Namespace) -> int:
    result = run_current_candidates_backfill_execution_manifest_status(root=args.root, output_dir=args.output_dir)
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Status artifact folder: {result.artifact_paths['artifact_dir']}")
    print(
        "Status report path: "
        f"{result.artifact_paths['current_candidates_backfill_execution_manifest_status_report']}"
    )
    print(f"status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_execution_manifest_id: {result.latest_execution_manifest_id}")
    print(f"health_status: {result.health_status}")
    print(f"row_count: {result.row_count}")
    print(f"ready_count: {result.ready_count}")
    print(f"blocked_count: {result.blocked_count}")
    print(f"blocked_missing_snapshot_count: {summary.get('blocked_missing_snapshot_count', '')}")
    print(f"blocked_snapshot_quality_count: {summary.get('blocked_snapshot_quality_count', '')}")
    print(f"blocked_universe_as_of_count: {summary.get('blocked_universe_as_of_count', '')}")
    print(f"blocked_plan_infeasible_count: {summary.get('blocked_plan_infeasible_count', '')}")
    print(f"next_manual_action: {result.next_manual_action}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(
        "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
        "order placement, message delivery, or network/API call was invoked."
    )
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


def _handle_signal_advisory(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    if args.output_dir:
        settings = settings.model_copy(
            update={
                "signal_advisory": settings.signal_advisory.model_copy(update={"output_dir": Path(args.output_dir)})
            }
        )
    result = build_signal_advisory_from_candidates(
        args.candidates,
        candidate_report_path=args.candidate_report,
        metadata_path=args.metadata,
        settings=settings,
    )
    print(f"signal_run_id: {result.signal_run_id}")
    print(f"source_candidate_run_id: {result.source_candidate_run_id}")
    print(f"signal_count: {result.signal_count}")
    print("advisory_action_counts:")
    for action, count in result.advisory_action_counts.items():
        if count:
            print(f"  {action}: {count}")
    print(f"signals_path: {result.artifact_paths['signals']}")
    print(f"report_path: {result.artifact_paths['signal_advisory_report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    if args.alert_preview:
        print(f"alert_preview_path: {result.artifact_paths['signal_alert_preview']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    print("No alert message was sent. No automated order placement was invoked.")
    return 0


def _handle_signal_semantics(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    if args.output_dir:
        settings = settings.model_copy(
            update={
                "signal_semantics": settings.signal_semantics.model_copy(update={"output_dir": Path(args.output_dir)})
            }
        )
    result = run_signal_semantics(
        args.input,
        input_type=args.input_type,
        metadata_path=args.metadata,
        profile=args.profile,
        snapshot_quality_status=args.snapshot_quality_status,
        data_quality_status=args.data_quality_status,
        settings=settings,
    )
    print(f"semantics_run_id: {result.semantics_run_id}")
    print(f"status: {result.status}")
    print(f"input_type: {result.input_type}")
    print(f"profile: {result.profile}")
    print(f"row_count: {result.row_count}")
    print("advisory_action_counts:")
    for action, count in result.action_counts.items():
        if count:
            print(f"  {action}: {count}")
    print(f"blocked_count: {result.action_counts.get('BLOCKED', 0)}")
    print(f"demo_only_count: {result.action_counts.get('DEMO_ONLY', 0)}")
    print(f"review_buy_candidate_count: {result.action_counts.get('REVIEW_BUY_CANDIDATE', 0)}")
    print(f"review_sell_candidate_count: {result.action_counts.get('REVIEW_SELL_CANDIDATE', 0)}")
    print(f"signal_semantics_path: {result.artifact_paths['signal_semantics']}")
    print(f"issues_path: {result.artifact_paths['signal_semantics_issues']}")
    print(f"report_path: {result.artifact_paths['signal_semantics_report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print("requires_manual_confirmation: True")
    print("auto_order_allowed: False")
    print("no_live_trading: True")
    print("no_broker_api: True")
    print("no_message_sent: True")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    print("No alert message was sent. No automated order placement was invoked.")
    return 0


def _handle_advisory_profile_calibration(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    if args.output_dir:
        settings = settings.model_copy(
            update={
                "advisory_profile_calibration": settings.advisory_profile_calibration.model_copy(
                    update={"output_dir": Path(args.output_dir)}
                )
            }
        )
    result = run_advisory_profile_calibration(
        args.input,
        input_type=args.input_type,
        profile=args.profile,
        snapshot_quality_status=args.snapshot_quality_status,
        data_quality_status=args.data_quality_status,
        settings=settings,
    )
    print(f"calibration_run_id: {result.calibration_run_id}")
    print(f"status: {result.status}")
    print(f"input_type: {result.input_type}")
    print(f"profile: {result.profile}")
    print(f"row_count: {result.row_count}")
    print(f"symbol_count: {result.symbol_count}")
    print("simulated_advisory_label_counts:")
    for label, count in result.label_counts.items():
        if count:
            print(f"  {label}: {count}")
    print(f"advisory_profile_calibration_path: {result.artifact_paths['advisory_profile_calibration']}")
    print(f"summary_path: {result.artifact_paths['advisory_profile_calibration_summary']}")
    print(f"issues_path: {result.artifact_paths['advisory_profile_calibration_issues']}")
    print(f"report_path: {result.artifact_paths['advisory_profile_calibration_report']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print("requires_manual_confirmation: True")
    print("auto_order_allowed: False")
    print("no_live_trading: True")
    print("no_broker_api: True")
    print("no_message_sent: True")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, or message delivery was invoked.")
    return 0


def _handle_advisory_profile_calibration_index(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"include_missing_metadata": bool(args.include_missing_metadata)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "advisory_profile_calibration_index": settings.advisory_profile_calibration_index.model_copy(
                update=updates
            )
        }
    )
    result = build_advisory_profile_calibration_index(settings=settings)
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index report path: {result.artifact_paths['advisory_profile_calibration_index_report']}")
    print(f"Index CSV path: {result.artifact_paths['advisory_profile_calibration_index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, or message delivery was invoked.")
    return 0


def _handle_advisory_profile_calibration_health(args: argparse.Namespace) -> int:
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
            "advisory_profile_calibration_health": settings.advisory_profile_calibration_health.model_copy(
                update=updates
            )
        }
    )
    result = check_advisory_profile_calibration_health(
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
    print(f"Report path: {result.artifact_paths['advisory_profile_calibration_health_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, or message delivery was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict and not args.allow_warn:
        return 1
    return 0


def _handle_advisory_profile_calibration_status(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "advisory_profile_calibration_status": settings.advisory_profile_calibration_status.model_copy(
                update=updates
            )
        }
    )
    result = run_advisory_profile_calibration_status(root=args.root, output_dir=args.output_dir, config=settings)
    print(f"Status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_calibration_run_id: {result.latest_calibration_run_id}")
    print(f"row_count: {result.row_count}")
    print(f"health_status: {result.health_status}")
    print(f"next_manual_action: {result.next_manual_action}")
    print(f"Report path: {result.artifact_paths['advisory_profile_calibration_status_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, or message delivery was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict:
        return 1
    return 0


def _handle_calibration_to_signal_semantics(args: argparse.Namespace) -> int:
    result = run_calibration_to_signal_semantics(
        calibration_root=args.calibration_root,
        semantics_config=args.semantics_config,
        output_dir=args.output_dir,
    )
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"proposal_run_id: {result.proposal_run_id}")
    print(f"status: {result.status}")
    print(f"calibration_run_count: {summary.get('calibration_run_count', 0)}")
    print(f"observed_review_buy_candidate_count: {summary.get('observed_review_buy_candidate_count', 0)}")
    print(f"observed_watch_count: {summary.get('observed_watch_count', 0)}")
    print(f"observed_blocked_count: {summary.get('observed_blocked_count', 0)}")
    print(f"semantics_reviewed_buy_min_score: {summary.get('semantics_reviewed_buy_min_score', '')}")
    print(f"semantics_watch_min_score: {summary.get('semantics_watch_min_score', '')}")
    print("proposal_categories:")
    for category in result.proposal_categories:
        print(f"  {category}")
    print(f"keep_current_defaults: {summary.get('keep_current_defaults', True)}")
    print(f"defaults_changed: {result.defaults_changed}")
    print(f"report_path: {result.artifact_paths['calibration_to_signal_semantics_report']}")
    print(f"summary_path: {result.artifact_paths['calibration_to_signal_semantics_summary']}")
    print(f"proposals_path: {result.artifact_paths['calibration_to_signal_semantics_proposals']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print("requires_manual_confirmation: True")
    print("auto_order_allowed: False")
    print("no_live_trading: True")
    print("no_broker_api: True")
    print("no_message_sent: True")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, message delivery, LLM API, or external API was invoked.")
    return 0


def _handle_calibration_to_signal_semantics_index(args: argparse.Namespace) -> int:
    result = build_calibration_to_signal_semantics_index(
        root=args.root,
        output_dir=args.output_dir,
        include_missing_metadata=bool(args.include_missing_metadata),
    )
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index report path: {result.artifact_paths['calibration_to_signal_semantics_index_report']}")
    print(f"Index CSV path: {result.artifact_paths['calibration_to_signal_semantics_index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, message delivery, LLM API, or external API was invoked.")
    return 0


def _handle_calibration_to_signal_semantics_health(args: argparse.Namespace) -> int:
    result = check_calibration_to_signal_semantics_health(
        index_path=args.index,
        root=None if args.index else args.root,
        output_dir=args.output_dir,
        settings={"strict": bool(args.strict)},
    )
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Report path: {result.artifact_paths['calibration_to_signal_semantics_health_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, message delivery, LLM API, or external API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict and not args.allow_warn:
        return 1
    return 0


def _handle_calibration_to_signal_semantics_status(args: argparse.Namespace) -> int:
    result = run_calibration_to_signal_semantics_status(
        root=args.root,
        output_dir=args.output_dir,
        config={"strict": bool(args.strict)},
    )
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_proposal_run_id: {result.latest_proposal_run_id}")
    print(f"health_status: {result.health_status}")
    print(f"proposal_categories: {summary.get('proposal_categories', '')}")
    print(f"defaults_changed: {summary.get('defaults_changed', '')}")
    print(f"calibration_run_count: {summary.get('calibration_run_count', 0)}")
    print(f"observed_review_buy_candidate_count: {summary.get('observed_review_buy_candidate_count', 0)}")
    print(f"observed_watch_count: {summary.get('observed_watch_count', 0)}")
    print(f"observed_blocked_count: {summary.get('observed_blocked_count', 0)}")
    print(f"next_manual_action: {result.next_manual_action}")
    print(f"Report path: {result.artifact_paths['calibration_to_signal_semantics_status_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, message delivery, LLM API, or external API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict:
        return 1
    return 0


def _handle_signal_semantics_index(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"include_missing_metadata": bool(args.include_missing_metadata)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={"signal_semantics_index": settings.signal_semantics_index.model_copy(update=updates)}
    )
    result = build_signal_semantics_index(settings=settings)
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index report path: {result.artifact_paths['signal_semantics_index_report']}")
    print(f"Index CSV path: {result.artifact_paths['signal_semantics_index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, or message delivery was invoked.")
    return 0


def _handle_signal_semantics_health(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.index:
        updates["index_path"] = Path(args.index)
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={"signal_semantics_health": settings.signal_semantics_health.model_copy(update=updates)}
    )
    result = check_signal_semantics_health(
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
    print(f"Report path: {result.artifact_paths['signal_semantics_health_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, or message delivery was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict and not args.allow_warn:
        return 1
    return 0


def _handle_signal_semantics_status(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={"signal_semantics_status": settings.signal_semantics_status.model_copy(update=updates)}
    )
    result = run_signal_semantics_status(root=args.root, output_dir=args.output_dir, config=settings)
    print(f"Status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_semantics_run_id: {result.latest_semantics_run_id}")
    print(f"row_count: {result.row_count}")
    print(f"health_status: {result.health_status}")
    print(f"next_manual_action: {result.next_manual_action}")
    print(f"Report path: {result.artifact_paths['signal_semantics_status_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, or message delivery was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict:
        return 1
    return 0


def _handle_signal_advisory_index(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"include_missing_metadata": bool(args.include_missing_metadata)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={"signal_advisory_index": settings.signal_advisory_index.model_copy(update=updates)}
    )
    result = build_signal_advisory_index(settings=settings)
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index report path: {result.artifact_paths['signal_advisory_index_report']}")
    print(f"Index CSV path: {result.artifact_paths['signal_advisory_index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, or message delivery was invoked.")
    return 0


def _handle_signal_advisory_health(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.index:
        updates["index_path"] = Path(args.index)
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={"signal_advisory_health": settings.signal_advisory_health.model_copy(update=updates)}
    )
    result = check_signal_advisory_health(
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
    print(f"Report path: {result.artifact_paths['signal_advisory_health_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, or message delivery was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict and not args.allow_warn:
        return 1
    return 0


def _handle_signal_advisory_status(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={"signal_advisory_status": settings.signal_advisory_status.model_copy(update=updates)}
    )
    result = run_signal_advisory_status(root=args.root, output_dir=args.output_dir, config=settings)
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_signal_run_id: {result.latest_signal_run_id}")
    print(f"signal_count: {result.signal_count}")
    print(f"health_status: {result.health_status}")
    print(f"semantics_policy_source: {summary.get('semantics_policy_source', '')}")
    print(f"semantics_policy_version: {summary.get('semantics_policy_version', '')}")
    print(f"semantics_action: {summary.get('semantics_action', '')}")
    print(f"semantics_provenance_present: {summary.get('semantics_provenance_present', '')}")
    print(
        "semantics_missing_provenance_legacy_warning_only: "
        f"{summary.get('semantics_missing_provenance_legacy_warning_only', '')}"
    )
    print(f"next_manual_action: {result.next_manual_action}")
    print(f"Report path: {result.artifact_paths['signal_advisory_status_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, or message delivery was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict:
        return 1
    return 0


def _handle_single_symbol_advisory(args: argparse.Namespace) -> int:
    if not args.candidates and not args.scored_dataset and not args.signals:
        raise ValueError("Provide at least one of --candidates, --scored-dataset, or --signals")
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    if args.output_dir:
        settings = settings.model_copy(
            update={
                "single_symbol_advisory": settings.single_symbol_advisory.model_copy(
                    update={"output_dir": Path(args.output_dir)}
                )
            }
        )
    result = build_single_symbol_advisory(
        args.symbol,
        candidates_path=args.candidates,
        scored_dataset_path=args.scored_dataset,
        factor_dataset_path=args.factor_dataset,
        signals_path=args.signals,
        metadata_path=args.metadata,
        snapshot_manifest_path=args.snapshot_manifest,
        advisory_date=args.date,
        alert_preview=bool(args.alert_preview),
        settings=settings,
    )
    print(f"advisory_run_id: {result.advisory_run_id}")
    print(f"status: {result.status}")
    print(f"symbol: {result.symbol}")
    print(f"advisory_action: {result.advisory_action}")
    print(f"final_score: {'' if result.final_score is None else result.final_score}")
    print(f"source_candidate_run_id: {result.source_candidate_run_id}")
    print(f"source_artifact_path: {result.source_artifact_path or ''}")
    print(f"report_path: {result.artifact_paths['single_symbol_advisory_report']}")
    print(f"csv_path: {result.artifact_paths['single_symbol_advisory_csv']}")
    print(f"json_path: {result.artifact_paths['single_symbol_advisory_json']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    if args.alert_preview and "alert_preview" in result.artifact_paths:
        print(f"alert_preview_path: {result.artifact_paths['alert_preview']}")
    print(f"requires_manual_confirmation: {result.requires_manual_confirmation}")
    print(f"auto_order_allowed: {result.auto_order_allowed}")
    print(f"no_live_trading: {result.no_live_trading}")
    print(f"no_broker_api: {result.no_broker_api}")
    print(f"no_message_sent: {result.no_message_sent}")
    if args.question_style:
        answer = build_single_symbol_advisory_answer(
            result,
            question=args.question,
            answer_style=args.answer_style,
            output_dir=args.answer_output_dir,
            settings=settings,
        )
        print(f"answer_run_id: {answer.answer_run_id}")
        print(f"answer_path: {answer.artifact_paths['single_symbol_advisory_answer']}")
        print(f"answer_json_path: {answer.artifact_paths['single_symbol_advisory_answer_json']}")
        print(f"answer_metadata_path: {answer.artifact_paths['metadata']}")
        print(f"short_answer: {answer.short_answer}")
    for issue in result.issues:
        print(f"{issue.severity}: {issue.category}: {issue.message}")
    print("No live trading or broker API was invoked.")
    print("No alert message was sent. No automated order placement was invoked.")
    return 0


def _handle_single_symbol_advisory_index(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"include_missing_metadata": bool(args.include_missing_metadata)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={"single_symbol_advisory_index": settings.single_symbol_advisory_index.model_copy(update=updates)}
    )
    result = build_single_symbol_advisory_index(settings=settings)
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index report path: {result.artifact_paths['single_symbol_advisory_index_report']}")
    print(f"Index CSV path: {result.artifact_paths['single_symbol_advisory_index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, or message delivery was invoked.")
    return 0


def _handle_single_symbol_advisory_health(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.index:
        updates["index_path"] = Path(args.index)
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={"single_symbol_advisory_health": settings.single_symbol_advisory_health.model_copy(update=updates)}
    )
    result = check_single_symbol_advisory_health(
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
    print(f"Report path: {result.artifact_paths['single_symbol_advisory_health_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, or message delivery was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict and not args.allow_warn:
        return 1
    return 0


def _handle_single_symbol_advisory_status(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={"single_symbol_advisory_status": settings.single_symbol_advisory_status.model_copy(update=updates)}
    )
    result = run_single_symbol_advisory_status(root=args.root, output_dir=args.output_dir, config=settings)
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_advisory_run_id: {result.latest_advisory_run_id}")
    print(f"latest_symbol: {result.latest_symbol}")
    print(f"latest_advisory_action: {result.latest_advisory_action}")
    print(f"health_status: {result.health_status}")
    print(f"semantics_policy_source: {summary.get('semantics_policy_source', '')}")
    print(f"semantics_policy_version: {summary.get('semantics_policy_version', '')}")
    print(f"semantics_action: {summary.get('semantics_action', '')}")
    print(f"semantics_provenance_present: {summary.get('semantics_provenance_present', '')}")
    print(
        "semantics_missing_provenance_legacy_warning_only: "
        f"{summary.get('semantics_missing_provenance_legacy_warning_only', '')}"
    )
    print(f"next_manual_action: {result.next_manual_action}")
    print(f"Report path: {result.artifact_paths['single_symbol_advisory_status_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, or message delivery was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict:
        return 1
    return 0


def _handle_single_symbol_advisory_answer_index(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"include_missing_metadata": bool(args.include_missing_metadata)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "single_symbol_advisory_answer_index": settings.single_symbol_advisory_answer_index.model_copy(
                update=updates
            )
        }
    )
    result = build_single_symbol_advisory_answer_index(settings=settings)
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index report path: {result.artifact_paths['single_symbol_advisory_answer_index_report']}")
    print(f"Index CSV path: {result.artifact_paths['single_symbol_advisory_answer_index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, LLM API, or message delivery was invoked.")
    return 0


def _handle_single_symbol_advisory_answer_health(args: argparse.Namespace) -> int:
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
            "single_symbol_advisory_answer_health": settings.single_symbol_advisory_answer_health.model_copy(
                update=updates
            )
        }
    )
    result = check_single_symbol_advisory_answer_health(
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
    print(f"Report path: {result.artifact_paths['single_symbol_advisory_answer_health_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, LLM API, or message delivery was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict and not args.allow_warn:
        return 1
    return 0


def _handle_single_symbol_advisory_answer_status(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "single_symbol_advisory_answer_status": settings.single_symbol_advisory_answer_status.model_copy(
                update=updates
            )
        }
    )
    result = run_single_symbol_advisory_answer_status(root=args.root, output_dir=args.output_dir, config=settings)
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_answer_run_id: {result.latest_answer_run_id}")
    print(f"latest_advisory_run_id: {result.latest_advisory_run_id}")
    print(f"latest_symbol: {result.latest_symbol}")
    print(f"latest_advisory_action: {result.latest_advisory_action}")
    print(f"health_status: {result.health_status}")
    print(f"semantics_policy_source: {summary.get('semantics_policy_source', '')}")
    print(f"semantics_policy_version: {summary.get('semantics_policy_version', '')}")
    print(f"semantics_action: {summary.get('semantics_action', '')}")
    print(f"semantics_provenance_present: {summary.get('semantics_provenance_present', '')}")
    print(
        "semantics_missing_provenance_legacy_warning_only: "
        f"{summary.get('semantics_missing_provenance_legacy_warning_only', '')}"
    )
    print(f"next_manual_action: {result.next_manual_action}")
    print(f"Report path: {result.artifact_paths['single_symbol_advisory_answer_status_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, LLM API, or message delivery was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict:
        return 1
    return 0


def _handle_advisory_conversation(args: argparse.Namespace) -> int:
    if not args.candidates and not args.scored_dataset and not args.signals:
        raise ValueError("Provide at least one of --candidates, --scored-dataset, or --signals")
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {}
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    if args.answer_style:
        updates["answer_style"] = args.answer_style
    if updates:
        settings = settings.model_copy(
            update={"advisory_conversation": settings.advisory_conversation.model_copy(update=updates)}
        )
    result = run_advisory_conversation(
        question=args.question,
        candidates_path=args.candidates,
        scored_dataset_path=args.scored_dataset,
        factor_dataset_path=args.factor_dataset,
        signals_path=args.signals,
        metadata_path=args.metadata,
        snapshot_manifest_path=args.snapshot_manifest,
        answer_style=args.answer_style,
        output_dir=args.output_dir,
        settings=settings,
    )
    print(f"conversation_run_id: {result.conversation_run_id}")
    print(f"status: {result.status}")
    print(f"original_question: {result.original_question}")
    print(f"parsed_symbol: {result.parsed_symbol}")
    print(f"parsed_intent: {result.parsed_intent}")
    print(f"parser_type: {result.parser_type}")
    print(f"advisory_action: {result.advisory_action}")
    print(f"answer_summary: {result.answer_summary}")
    print(f"linked_advisory_run_id: {result.linked_advisory_run_id}")
    print(f"linked_answer_run_id: {result.linked_answer_run_id}")
    print(f"linked_answer_markdown_path: {result.linked_answer_markdown_path}")
    print(f"report_path: {result.artifact_paths['advisory_conversation_report']}")
    print(f"json_path: {result.artifact_paths['advisory_conversation_json']}")
    print(f"metadata_path: {result.artifact_paths['metadata']}")
    print(f"requires_manual_confirmation: {result.requires_manual_confirmation}")
    print(f"auto_order_allowed: {result.auto_order_allowed}")
    print(f"no_live_trading: {result.no_live_trading}")
    print(f"no_broker_api: {result.no_broker_api}")
    print(f"no_message_sent: {result.no_message_sent}")
    print(f"llm_api_called: {result.llm_api_called}")
    print(f"external_api_called: {result.external_api_called}")
    if result.parse_result.issue:
        print(f"WARNING: {result.parse_result.issue}")
    print("No live trading, broker API, order placement, LLM API, external API, or message delivery was invoked.")
    return 0


def _handle_advisory_conversation_index(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"include_missing_metadata": bool(args.include_missing_metadata)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={"advisory_conversation_index": settings.advisory_conversation_index.model_copy(update=updates)}
    )
    result = build_advisory_conversation_index(settings=settings)
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index report path: {result.artifact_paths['advisory_conversation_index_report']}")
    print(f"Index CSV path: {result.artifact_paths['advisory_conversation_index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, LLM/API call, external API call, or message delivery was invoked.")
    return 0


def _handle_advisory_conversation_health(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.index:
        updates["index_path"] = Path(args.index)
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={"advisory_conversation_health": settings.advisory_conversation_health.model_copy(update=updates)}
    )
    result = check_advisory_conversation_health(
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
    print(f"Report path: {result.artifact_paths['advisory_conversation_health_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, LLM/API call, external API call, or message delivery was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict and not args.allow_warn:
        return 1
    return 0


def _handle_advisory_conversation_status(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={"advisory_conversation_status": settings.advisory_conversation_status.model_copy(update=updates)}
    )
    result = run_advisory_conversation_status(root=args.root, output_dir=args.output_dir, config=settings)
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_conversation_run_id: {result.latest_conversation_run_id}")
    print(f"latest_original_question: {result.latest_original_question}")
    print(f"latest_parsed_symbol: {result.latest_parsed_symbol}")
    print(f"latest_parsed_intent: {result.latest_parsed_intent}")
    print(f"latest_advisory_action: {result.latest_advisory_action}")
    print(f"health_status: {result.health_status}")
    print(f"parser_type: {summary.get('parser_type', '')}")
    print(f"llm_api_called: {summary.get('llm_api_called', False)}")
    print(f"no_message_sent: {summary.get('no_message_sent', False)}")
    print(f"no_live_trading: {summary.get('no_live_trading', False)}")
    print(f"no_broker_api: {summary.get('no_broker_api', False)}")
    print(f"auto_order_allowed: {summary.get('auto_order_allowed', False)}")
    print(f"semantics_policy_source: {summary.get('semantics_policy_source', '')}")
    print(f"semantics_policy_version: {summary.get('semantics_policy_version', '')}")
    print(f"semantics_action: {summary.get('semantics_action', '')}")
    print(f"semantics_provenance_present: {summary.get('semantics_provenance_present', '')}")
    print(
        "semantics_missing_provenance_legacy_warning_only: "
        f"{summary.get('semantics_missing_provenance_legacy_warning_only', '')}"
    )
    print(f"linked_answer_markdown_path: {summary.get('linked_answer_markdown_path', '')}")
    print(f"next_manual_action: {result.next_manual_action}")
    print(f"Report path: {result.artifact_paths['advisory_conversation_status_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading, broker API, order placement, LLM/API call, external API call, or message delivery was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict:
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
    result = reconcile_paper_fills(
        read_csv_preserve_symbol_columns(decisions_path),
        read_csv_preserve_symbol_columns(fills_path),
        settings=settings,
        artifact_scope=args.artifact_scope,
        diagnostic_reason=args.diagnostic_reason,
    )
    print(f"Reconciliation status: {result.status}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(f"artifact_scope: {result.audit_metadata.get('artifact_scope', 'active')}")
    if result.audit_metadata.get("diagnostic_reason"):
        print(f"diagnostic_reason: {result.audit_metadata['diagnostic_reason']}")
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
    decisions_frame = read_csv_preserve_symbol_columns(decisions_path)
    updates_frame = read_csv_preserve_symbol_columns(updates_path)
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
        read_csv_preserve_symbol_columns(updates_path),
        decisions=read_csv_preserve_symbol_columns(decisions_path) if decisions_path is not None else None,
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
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"watch_only_count: {summary.get('watch_only_count', 0)}")
    print(f"approved_count: {summary.get('approved_count', 0)}")
    print(f"open_position_count: {summary.get('open_position_count', 0)}")
    print(f"closed_trade_count: {summary.get('closed_trade_count', 0)}")
    print(f"paper_demo_validated: {summary.get('paper_demo_validated', False)}")
    print(f"diagnostic_reconciliation_failure_count: {summary.get('diagnostic_reconciliation_failure_count', 0)}")
    print(f"active_reconciliation_error_count: {summary.get('active_reconciliation_error_count', 0)}")
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
    if args.historical_backfill_root:
        updates["historical_backfill_root"] = Path(args.historical_backfill_root)
    if args.market_cache_export_policy_root:
        updates["market_cache_export_policy_root"] = Path(args.market_cache_export_policy_root)
    if args.market_cache_export_root:
        updates["market_cache_export_root"] = Path(args.market_cache_export_root)
    if args.data_preparation_root:
        updates["data_preparation_root"] = Path(args.data_preparation_root)
    if args.current_candidates_root:
        updates["current_candidates_root"] = Path(args.current_candidates_root)
    if args.current_candidates_backfill_plan_root:
        updates["current_candidates_backfill_plan_root"] = Path(args.current_candidates_backfill_plan_root)
    if args.current_candidates_backfill_execution_manifest_root:
        updates["current_candidates_backfill_execution_manifest_root"] = Path(
            args.current_candidates_backfill_execution_manifest_root
        )
    if args.pit_universe_overlay_plan_root:
        updates["point_in_time_universe_overlay_plan_root"] = Path(args.pit_universe_overlay_plan_root)
    if args.pit_universe_overlay_review_root:
        updates["point_in_time_universe_overlay_review_root"] = Path(args.pit_universe_overlay_review_root)
    if args.pit_universe_overlay_export_readiness_root:
        updates["point_in_time_universe_overlay_export_readiness_root"] = Path(
            args.pit_universe_overlay_export_readiness_root
        )
    if args.pit_universe_export_staging_root:
        updates["point_in_time_universe_export_staging_root"] = Path(args.pit_universe_export_staging_root)
    if args.pit_universe_evidence_completion_helper_root:
        updates["point_in_time_universe_evidence_completion_helper_root"] = Path(
            args.pit_universe_evidence_completion_helper_root
        )
    if args.pit_universe_evidence_review_worklist_root:
        updates["point_in_time_universe_evidence_review_worklist_root"] = Path(
            args.pit_universe_evidence_review_worklist_root
        )
    if args.pit_universe_evidence_update_ingestion_root:
        updates["point_in_time_universe_evidence_update_ingestion_root"] = Path(
            args.pit_universe_evidence_update_ingestion_root
        )
    if args.universe_profile_policy_audit_root:
        updates["universe_profile_policy_audit_root"] = Path(args.universe_profile_policy_audit_root)
    if args.universe_profile_split_worklist_plan_root:
        updates["universe_profile_split_worklist_plan_root"] = Path(args.universe_profile_split_worklist_plan_root)
    if args.reviewed_replacement_worklist_plan_root:
        updates["reviewed_replacement_worklist_plan_root"] = Path(args.reviewed_replacement_worklist_plan_root)
    if args.reviewed_replacement_worklist_acceptance_root:
        updates["reviewed_replacement_worklist_acceptance_root"] = Path(
            args.reviewed_replacement_worklist_acceptance_root
        )
    if args.reviewed_replacement_worklist_activation_root:
        updates["reviewed_replacement_worklist_activation_root"] = Path(
            args.reviewed_replacement_worklist_activation_root
        )
    if args.activated_replacement_worklist_evidence_update_plan_root:
        updates["activated_replacement_worklist_evidence_update_plan_root"] = Path(
            args.activated_replacement_worklist_evidence_update_plan_root
        )
    if args.advisory_profile_calibration_root:
        updates["advisory_profile_calibration_root"] = Path(args.advisory_profile_calibration_root)
    if args.calibration_to_signal_semantics_root:
        updates["calibration_to_signal_semantics_root"] = Path(args.calibration_to_signal_semantics_root)
    if args.signal_semantics_root:
        updates["signal_semantics_root"] = Path(args.signal_semantics_root)
    if args.single_symbol_advisory_root:
        updates["single_symbol_advisory_root"] = Path(args.single_symbol_advisory_root)
    if args.single_symbol_advisory_answer_root:
        updates["single_symbol_advisory_answer_root"] = Path(args.single_symbol_advisory_answer_root)
    if args.advisory_conversation_root:
        updates["advisory_conversation_root"] = Path(args.advisory_conversation_root)
    if args.market_update_handoff_root:
        updates["market_update_handoff_root"] = Path(args.market_update_handoff_root)
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
        historical_backfill_root=args.historical_backfill_root,
        market_cache_export_policy_root=args.market_cache_export_policy_root,
        market_cache_export_root=args.market_cache_export_root,
        data_preparation_root=args.data_preparation_root,
        current_candidates_root=args.current_candidates_root,
        current_candidates_backfill_plan_root=args.current_candidates_backfill_plan_root,
        current_candidates_backfill_execution_manifest_root=(
            args.current_candidates_backfill_execution_manifest_root
        ),
        pit_universe_overlay_plan_root=args.pit_universe_overlay_plan_root,
        pit_universe_overlay_review_root=args.pit_universe_overlay_review_root,
        pit_universe_overlay_export_readiness_root=args.pit_universe_overlay_export_readiness_root,
        pit_universe_export_staging_root=args.pit_universe_export_staging_root,
        pit_universe_evidence_completion_helper_root=args.pit_universe_evidence_completion_helper_root,
        pit_universe_evidence_review_worklist_root=args.pit_universe_evidence_review_worklist_root,
        pit_universe_evidence_update_ingestion_root=args.pit_universe_evidence_update_ingestion_root,
        pit_evidence_checklist_validator_root=args.pit_evidence_checklist_validator_root,
        pit_evidence_policy_profile_comparison_root=args.pit_evidence_policy_profile_comparison_root,
        pit_official_status_evidence_packet_root=args.pit_official_status_evidence_packet_root,
        pit_official_status_evidence_packet_enrichment_root=(
            args.pit_official_status_evidence_packet_enrichment_root
        ),
        reviewer_no_hit_source_coverage_acceptance_root=(
            args.reviewer_no_hit_source_coverage_acceptance_root
        ),
        reviewer_no_hit_acceptance_downstream_impact_root=(
            args.reviewer_no_hit_acceptance_downstream_impact_root
        ),
        first_batch_reviewer_evidence_completion_plan_root=(
            args.first_batch_reviewer_evidence_completion_plan_root
        ),
        first_batch_partial_completion_impact_root=args.first_batch_partial_completion_impact_root,
        material_pit_evidence_gate_closure_plan_root=args.material_pit_evidence_gate_closure_plan_root,
        one_row_material_evidence_fill_package_root=args.one_row_material_evidence_fill_package_root,
        universe_profile_policy_audit_root=args.universe_profile_policy_audit_root,
        universe_profile_split_worklist_plan_root=args.universe_profile_split_worklist_plan_root,
        reviewed_replacement_worklist_plan_root=args.reviewed_replacement_worklist_plan_root,
        reviewed_replacement_worklist_acceptance_root=args.reviewed_replacement_worklist_acceptance_root,
        reviewed_replacement_worklist_activation_root=args.reviewed_replacement_worklist_activation_root,
        activated_replacement_worklist_evidence_update_plan_root=(
            args.activated_replacement_worklist_evidence_update_plan_root
        ),
        advisory_profile_calibration_root=args.advisory_profile_calibration_root,
        calibration_to_signal_semantics_root=args.calibration_to_signal_semantics_root,
        signal_semantics_root=args.signal_semantics_root,
        single_symbol_advisory_root=args.single_symbol_advisory_root,
        single_symbol_advisory_answer_root=args.single_symbol_advisory_answer_root,
        advisory_conversation_root=args.advisory_conversation_root,
        market_update_handoff_root=args.market_update_handoff_root,
        paper_trading_root=args.paper_trading_root,
        decision_date=args.decision_date,
        universe_name=args.universe,
        output_dir=args.output_dir,
        config=settings,
    )
    print(f"Research status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_decision_date: {result.latest_decision_date}")
    print(f"active_snapshot_chain: {result.active_snapshot_chain}")
    print(f"linked_snapshot_quality_status: {result.linked_snapshot_quality_status}")
    print(f"active_snapshot_warning_count: {result.active_snapshot_warning_count}")
    print(f"active_snapshot_error_count: {result.active_snapshot_error_count}")
    print(f"stale_snapshot_warning_count: {result.stale_snapshot_warning_count}")
    print(f"unrelated_snapshot_warning_count: {result.unrelated_snapshot_warning_count}")
    print(f"latest_historical_backfill_id: {result.latest_historical_backfill_id}")
    print(f"historical_backfill_status: {result.historical_backfill_status}")
    print(f"historical_backfill_stage: {result.historical_backfill_stage}")
    print(f"historical_backfill_cache_write_occurred: {result.historical_backfill_cache_write_occurred}")
    print(f"historical_backfill_cache_write_partial: {result.historical_backfill_cache_write_partial}")
    print(f"historical_backfill_accepted_task_count: {result.historical_backfill_accepted_task_count}")
    print(f"historical_backfill_rejected_task_count: {result.historical_backfill_rejected_task_count}")
    print(f"historical_backfill_preflight_rejected_count: {result.historical_backfill_preflight_rejected_count}")
    print(f"historical_backfill_comparison_failed_count: {result.historical_backfill_comparison_failed_count}")
    print(f"historical_backfill_rejected_symbols: {result.historical_backfill_rejected_symbols}")
    print(f"historical_backfill_rejected_issue_categories: {result.historical_backfill_rejected_issue_categories}")
    print(f"latest_market_cache_export_plan_id: {result.latest_market_cache_export_plan_id}")
    print(f"market_cache_export_plan_status: {result.market_cache_export_plan_status}")
    print(f"market_cache_export_plan_stage: {result.market_cache_export_plan_stage}")
    print(f"market_cache_export_plan_comparison_pass_count: {result.market_cache_export_plan_comparison_pass_count}")
    print(f"market_cache_export_plan_comparison_warn_count: {result.market_cache_export_plan_comparison_warn_count}")
    print(f"market_cache_export_plan_comparison_fail_count: {result.market_cache_export_plan_comparison_fail_count}")
    print(
        "market_cache_export_plan_comparison_unavailable_count: "
        f"{result.market_cache_export_plan_comparison_unavailable_count}"
    )
    print(f"market_cache_export_plan_downstream_export_id: {result.market_cache_export_plan_downstream_export_id}")
    print(
        "market_cache_export_plan_downstream_snapshot_quality_status: "
        f"{result.market_cache_export_plan_downstream_snapshot_quality_status}"
    )
    print(f"latest_market_cache_export_id: {result.latest_market_cache_export_id}")
    print(f"market_cache_export_status: {result.market_cache_export_status}")
    print(f"market_cache_export_stage: {result.market_cache_export_stage}")
    print(f"market_cache_export_pipeline_id: {result.market_cache_export_pipeline_id}")
    print(f"market_cache_export_snapshot_quality_status: {result.market_cache_export_snapshot_quality_status}")
    print(f"latest_current_candidates_backfill_plan_id: {result.latest_current_candidates_backfill_plan_id}")
    print(f"current_candidates_backfill_plan_status: {result.current_candidates_backfill_plan_status}")
    print(f"current_candidates_backfill_plan_stage: {result.current_candidates_backfill_plan_stage}")
    print(
        "current_candidates_backfill_plan_health_status: "
        f"{result.current_candidates_backfill_plan_health_status}"
    )
    print(
        "current_candidates_backfill_plan_selected_date_count: "
        f"{result.current_candidates_backfill_plan_selected_date_count}"
    )
    print(
        "current_candidates_backfill_plan_first_signal_date: "
        f"{result.current_candidates_backfill_plan_first_signal_date}"
    )
    print(
        "current_candidates_backfill_plan_last_signal_date: "
        f"{result.current_candidates_backfill_plan_last_signal_date}"
    )
    print(
        "current_candidates_backfill_plan_warmup_trading_days: "
        f"{result.current_candidates_backfill_plan_warmup_trading_days}"
    )
    print(
        "current_candidates_backfill_plan_forward_horizon_summary: "
        f"{result.current_candidates_backfill_plan_forward_horizon_summary}"
    )
    print(
        "current_candidates_backfill_plan_legacy_plan_count: "
        f"{result.current_candidates_backfill_plan_legacy_plan_count}"
    )
    print(
        "current_candidates_backfill_plan_stale_plan_warning_count: "
        f"{result.current_candidates_backfill_plan_stale_plan_warning_count}"
    )
    print(
        "current_candidates_backfill_plan_active_plan_issue_count: "
        f"{result.current_candidates_backfill_plan_active_plan_issue_count}"
    )
    print(
        "current_candidates_backfill_plan_active_plan_error_count: "
        f"{result.current_candidates_backfill_plan_active_plan_error_count}"
    )
    print(
        "current_candidates_backfill_plan_legacy_missing_warmup_count: "
        f"{result.current_candidates_backfill_plan_legacy_missing_warmup_count}"
    )
    print(
        "current_candidates_backfill_plan_latest_plan_is_warmup_aware: "
        f"{result.current_candidates_backfill_plan_latest_plan_is_warmup_aware}"
    )
    print(f"current_candidates_backfill_plan_report_path: {result.current_candidates_backfill_plan_report_path}")
    print(f"current_candidates_backfill_plan_next_action: {result.current_candidates_backfill_plan_next_action}")
    print(
        "latest_current_candidates_backfill_execution_manifest_id: "
        f"{result.latest_current_candidates_backfill_execution_manifest_id}"
    )
    print(
        "current_candidates_backfill_execution_manifest_status: "
        f"{result.current_candidates_backfill_execution_manifest_status}"
    )
    print(
        "current_candidates_backfill_execution_manifest_stage: "
        f"{result.current_candidates_backfill_execution_manifest_stage}"
    )
    print(
        "current_candidates_backfill_execution_manifest_health_status: "
        f"{result.current_candidates_backfill_execution_manifest_health_status}"
    )
    print(
        "current_candidates_backfill_execution_manifest_plan_id: "
        f"{result.current_candidates_backfill_execution_manifest_plan_id}"
    )
    print(
        "current_candidates_backfill_execution_manifest_row_count: "
        f"{result.current_candidates_backfill_execution_manifest_row_count}"
    )
    print(
        "current_candidates_backfill_execution_manifest_ready_count: "
        f"{result.current_candidates_backfill_execution_manifest_ready_count}"
    )
    print(
        "current_candidates_backfill_execution_manifest_blocked_count: "
        f"{result.current_candidates_backfill_execution_manifest_blocked_count}"
    )
    print(
        "current_candidates_backfill_execution_manifest_blocked_missing_snapshot_count: "
        f"{result.current_candidates_backfill_execution_manifest_blocked_missing_snapshot_count}"
    )
    print(
        "current_candidates_backfill_execution_manifest_blocked_snapshot_quality_count: "
        f"{result.current_candidates_backfill_execution_manifest_blocked_snapshot_quality_count}"
    )
    print(
        "current_candidates_backfill_execution_manifest_blocked_universe_as_of_count: "
        f"{result.current_candidates_backfill_execution_manifest_blocked_universe_as_of_count}"
    )
    print(
        "current_candidates_backfill_execution_manifest_blocked_plan_infeasible_count: "
        f"{result.current_candidates_backfill_execution_manifest_blocked_plan_infeasible_count}"
    )
    print(
        "current_candidates_backfill_execution_manifest_report_path: "
        f"{result.current_candidates_backfill_execution_manifest_report_path}"
    )
    print(
        "current_candidates_backfill_execution_manifest_next_action: "
        f"{result.current_candidates_backfill_execution_manifest_next_action}"
    )
    print(f"latest_pit_universe_overlay_plan_id: {result.latest_pit_universe_overlay_plan_id}")
    print(f"pit_universe_overlay_plan_status: {result.pit_universe_overlay_plan_status}")
    print(f"pit_universe_overlay_plan_stage: {result.pit_universe_overlay_plan_stage}")
    print(f"pit_universe_overlay_plan_health_status: {result.pit_universe_overlay_plan_health_status}")
    print(f"pit_universe_overlay_plan_row_count: {result.pit_universe_overlay_plan_row_count}")
    print(f"pit_universe_overlay_plan_signal_date_count: {result.pit_universe_overlay_plan_signal_date_count}")
    print(f"pit_universe_overlay_plan_symbol_count: {result.pit_universe_overlay_plan_symbol_count}")
    print(
        "pit_universe_overlay_plan_needs_manual_review_count: "
        f"{result.pit_universe_overlay_plan_needs_manual_review_count}"
    )
    print(
        "pit_universe_overlay_plan_valid_for_signal_date_count: "
        f"{result.pit_universe_overlay_plan_valid_for_signal_date_count}"
    )
    print(
        "pit_universe_overlay_plan_survivorship_bias_warning_count: "
        f"{result.pit_universe_overlay_plan_survivorship_bias_warning_count}"
    )
    print(f"pit_universe_overlay_plan_report_path: {result.pit_universe_overlay_plan_report_path}")
    print(f"pit_universe_overlay_plan_next_action: {result.pit_universe_overlay_plan_next_action}")
    print(f"latest_pit_universe_overlay_review_id: {result.latest_pit_universe_overlay_review_id}")
    print(f"pit_universe_overlay_review_status: {result.pit_universe_overlay_review_status}")
    print(f"pit_universe_overlay_review_stage: {result.pit_universe_overlay_review_stage}")
    print(f"pit_universe_overlay_review_health_status: {result.pit_universe_overlay_review_health_status}")
    print(f"pit_universe_overlay_review_approved_count: {result.pit_universe_overlay_review_approved_count}")
    print(
        "pit_universe_overlay_review_valid_for_signal_date_count: "
        f"{result.pit_universe_overlay_review_valid_for_signal_date_count}"
    )
    print(
        "pit_universe_overlay_review_needs_more_evidence_count: "
        f"{result.pit_universe_overlay_review_needs_more_evidence_count}"
    )
    print(
        "pit_universe_overlay_review_unresolved_survivorship_warning_count: "
        f"{result.pit_universe_overlay_review_unresolved_survivorship_warning_count}"
    )
    print(f"pit_universe_overlay_review_report_path: {result.pit_universe_overlay_review_report_path}")
    print(f"pit_universe_overlay_review_next_action: {result.pit_universe_overlay_review_next_action}")
    print(f"latest_pit_universe_export_readiness_id: {result.latest_pit_universe_export_readiness_id}")
    print(f"pit_universe_export_readiness_status: {result.pit_universe_export_readiness_status}")
    print(f"pit_universe_export_readiness_stage: {result.pit_universe_export_readiness_stage}")
    print(
        "pit_universe_export_readiness_health_status: "
        f"{result.pit_universe_export_readiness_health_status}"
    )
    print(f"pit_universe_export_readiness_review_id: {result.pit_universe_export_readiness_review_id}")
    print(
        "pit_universe_export_readiness_approved_count: "
        f"{result.pit_universe_export_readiness_approved_count}"
    )
    print(
        "pit_universe_export_readiness_export_ready_count: "
        f"{result.pit_universe_export_readiness_export_ready_count}"
    )
    print(
        "pit_universe_export_readiness_blocked_count: "
        f"{result.pit_universe_export_readiness_blocked_count}"
    )
    print(
        "pit_universe_export_readiness_no_approved_rows: "
        f"{result.pit_universe_export_readiness_no_approved_rows}"
    )
    print(
        "pit_universe_export_readiness_missing_required_columns_count: "
        f"{result.pit_universe_export_readiness_missing_required_columns_count}"
    )
    print(
        "pit_universe_export_readiness_unresolved_survivorship_warning_count: "
        f"{result.pit_universe_export_readiness_unresolved_survivorship_warning_count}"
    )
    print(f"pit_universe_export_readiness_report_path: {result.pit_universe_export_readiness_report_path}")
    print(f"pit_universe_export_readiness_next_action: {result.pit_universe_export_readiness_next_action}")
    print(f"latest_pit_universe_export_staging_id: {result.latest_pit_universe_export_staging_id}")
    print(f"pit_universe_export_staging_status: {result.pit_universe_export_staging_status}")
    print(f"pit_universe_export_staging_stage: {result.pit_universe_export_staging_stage}")
    print(f"pit_universe_export_staging_health_status: {result.pit_universe_export_staging_health_status}")
    print(
        "pit_universe_export_staging_export_readiness_id: "
        f"{result.pit_universe_export_staging_export_readiness_id}"
    )
    print(f"pit_universe_export_staging_review_id: {result.pit_universe_export_staging_review_id}")
    print(
        "pit_universe_export_staging_export_ready_input_count: "
        f"{result.pit_universe_export_staging_export_ready_input_count}"
    )
    print(
        "pit_universe_export_staging_staged_row_count: "
        f"{result.pit_universe_export_staging_staged_row_count}"
    )
    print(f"pit_universe_export_staging_blocked_count: {result.pit_universe_export_staging_blocked_count}")
    print(
        "pit_universe_export_staging_source_is_diagnostic: "
        f"{result.pit_universe_export_staging_source_is_diagnostic}"
    )
    print(f"pit_universe_export_staging_no_ready_rows: {result.pit_universe_export_staging_no_ready_rows}")
    print(f"pit_universe_export_staging_report_path: {result.pit_universe_export_staging_report_path}")
    print(f"pit_universe_export_staging_next_action: {result.pit_universe_export_staging_next_action}")
    print(f"latest_pit_universe_evidence_helper_id: {result.latest_pit_universe_evidence_helper_id}")
    print(f"pit_universe_evidence_helper_status: {result.pit_universe_evidence_helper_status}")
    print(f"pit_universe_evidence_helper_stage: {result.pit_universe_evidence_helper_stage}")
    print(
        "pit_universe_evidence_helper_health_status: "
        f"{result.pit_universe_evidence_helper_health_status}"
    )
    print(f"pit_universe_evidence_helper_review_id: {result.pit_universe_evidence_helper_review_id}")
    print(f"pit_universe_evidence_helper_row_count: {result.pit_universe_evidence_helper_row_count}")
    print(
        "pit_universe_evidence_helper_needs_evidence_count: "
        f"{result.pit_universe_evidence_helper_needs_evidence_count}"
    )
    print(
        "pit_universe_evidence_helper_rows_with_base_hints_count: "
        f"{result.pit_universe_evidence_helper_rows_with_base_hints_count}"
    )
    print(
        "pit_universe_evidence_helper_future_dated_hint_count: "
        f"{result.pit_universe_evidence_helper_future_dated_hint_count}"
    )
    print(
        "pit_universe_evidence_helper_authoritative_hint_count: "
        f"{result.pit_universe_evidence_helper_authoritative_hint_count}"
    )
    print(f"pit_universe_evidence_helper_report_path: {result.pit_universe_evidence_helper_report_path}")
    print(f"pit_universe_evidence_helper_next_action: {result.pit_universe_evidence_helper_next_action}")
    print(f"latest_pit_universe_evidence_worklist_id: {result.latest_pit_universe_evidence_worklist_id}")
    print(f"pit_universe_evidence_worklist_status: {result.pit_universe_evidence_worklist_status}")
    print(f"pit_universe_evidence_worklist_stage: {result.pit_universe_evidence_worklist_stage}")
    print(
        "pit_universe_evidence_worklist_health_status: "
        f"{result.pit_universe_evidence_worklist_health_status}"
    )
    print(f"pit_universe_evidence_worklist_review_id: {result.pit_universe_evidence_worklist_review_id}")
    print(f"pit_universe_evidence_worklist_helper_id: {result.pit_universe_evidence_worklist_helper_id}")
    print(f"pit_universe_evidence_worklist_row_count: {result.pit_universe_evidence_worklist_row_count}")
    print(f"pit_universe_evidence_worklist_symbol_count: {result.pit_universe_evidence_worklist_symbol_count}")
    print(
        "pit_universe_evidence_worklist_signal_date_count: "
        f"{result.pit_universe_evidence_worklist_signal_date_count}"
    )
    print(
        "pit_universe_evidence_worklist_needs_evidence_count: "
        f"{result.pit_universe_evidence_worklist_needs_evidence_count}"
    )
    print(
        "pit_universe_evidence_worklist_future_dated_hint_count: "
        f"{result.pit_universe_evidence_worklist_future_dated_hint_count}"
    )
    print(f"pit_universe_evidence_worklist_report_path: {result.pit_universe_evidence_worklist_report_path}")
    print(f"pit_universe_evidence_worklist_next_action: {result.pit_universe_evidence_worklist_next_action}")
    print(
        "latest_pit_universe_evidence_update_ingestion_id: "
        f"{result.latest_pit_universe_evidence_update_ingestion_id}"
    )
    print(
        "pit_universe_evidence_update_ingestion_status: "
        f"{result.pit_universe_evidence_update_ingestion_status}"
    )
    print(
        "pit_universe_evidence_update_ingestion_stage: "
        f"{result.pit_universe_evidence_update_ingestion_stage}"
    )
    print(
        "pit_universe_evidence_update_ingestion_health_status: "
        f"{result.pit_universe_evidence_update_ingestion_health_status}"
    )
    print(
        "pit_universe_evidence_update_ingestion_row_count: "
        f"{result.pit_universe_evidence_update_ingestion_row_count}"
    )
    print(
        "pit_universe_evidence_update_ingestion_ready_for_review_update_count: "
        f"{result.pit_universe_evidence_update_ingestion_ready_for_review_update_count}"
    )
    print(
        "pit_universe_evidence_update_ingestion_blocked_count: "
        f"{result.pit_universe_evidence_update_ingestion_blocked_count}"
    )
    print(
        "pit_universe_evidence_update_ingestion_approval_requested_count: "
        f"{result.pit_universe_evidence_update_ingestion_approval_requested_count}"
    )
    print(
        "pit_universe_evidence_update_ingestion_approved_ready_count: "
        f"{result.pit_universe_evidence_update_ingestion_approved_ready_count}"
    )
    print(
        "pit_universe_evidence_update_ingestion_duplicate_identity_count: "
        f"{result.pit_universe_evidence_update_ingestion_duplicate_identity_count}"
    )
    print(
        "pit_universe_evidence_update_ingestion_suggested_copy_risk_count: "
        f"{result.pit_universe_evidence_update_ingestion_suggested_copy_risk_count}"
    )
    print(
        "pit_universe_evidence_update_ingestion_report_path: "
        f"{result.pit_universe_evidence_update_ingestion_report_path}"
    )
    print(
        "pit_universe_evidence_update_ingestion_review_updates_path: "
        f"{result.pit_universe_evidence_update_ingestion_review_updates_path}"
    )
    print(
        "pit_universe_evidence_update_ingestion_next_action: "
        f"{result.pit_universe_evidence_update_ingestion_next_action}"
    )
    print(f"latest_pit_evidence_checklist_validator_id: {result.latest_pit_evidence_checklist_validator_id}")
    print(f"pit_evidence_checklist_validator_status: {result.pit_evidence_checklist_validator_status}")
    print(f"pit_evidence_checklist_validator_stage: {result.pit_evidence_checklist_validator_stage}")
    print(
        "pit_evidence_checklist_validator_health_status: "
        f"{result.pit_evidence_checklist_validator_health_status}"
    )
    print(f"pit_evidence_checklist_validator_row_count: {result.pit_evidence_checklist_validator_row_count}")
    print(
        "pit_evidence_checklist_validator_checklist_pass_count: "
        f"{result.pit_evidence_checklist_validator_checklist_pass_count}"
    )
    print(f"pit_evidence_checklist_validator_blocked_count: {result.pit_evidence_checklist_validator_blocked_count}")
    print(
        "pit_evidence_checklist_validator_stock_core_blocked_count: "
        f"{result.pit_evidence_checklist_validator_stock_core_blocked_count}"
    )
    print(
        "pit_evidence_checklist_validator_etf_core_blocked_count: "
        f"{result.pit_evidence_checklist_validator_etf_core_blocked_count}"
    )
    print(f"pit_evidence_checklist_validator_report_path: {result.pit_evidence_checklist_validator_report_path}")
    print(f"pit_evidence_checklist_validator_next_action: {result.pit_evidence_checklist_validator_next_action}")
    print(
        "latest_pit_evidence_policy_profile_comparison_id: "
        f"{result.latest_pit_evidence_policy_profile_comparison_id}"
    )
    print(
        "pit_evidence_policy_profile_comparison_status: "
        f"{result.pit_evidence_policy_profile_comparison_status}"
    )
    print(
        "pit_evidence_policy_profile_comparison_stage: "
        f"{result.pit_evidence_policy_profile_comparison_stage}"
    )
    print(
        "pit_evidence_policy_profile_comparison_health_status: "
        f"{result.pit_evidence_policy_profile_comparison_health_status}"
    )
    print(
        "pit_evidence_policy_profile_comparison_profile_name: "
        f"{result.pit_evidence_policy_profile_comparison_profile_name}"
    )
    print(
        "pit_evidence_policy_profile_comparison_row_count: "
        f"{result.pit_evidence_policy_profile_comparison_row_count}"
    )
    print(
        "pit_evidence_policy_profile_comparison_strict_pass_count: "
        f"{result.pit_evidence_policy_profile_comparison_strict_pass_count}"
    )
    print(
        "pit_evidence_policy_profile_comparison_eod_low_budget_pass_count: "
        f"{result.pit_evidence_policy_profile_comparison_eod_low_budget_pass_count}"
    )
    print(
        "pit_evidence_policy_profile_comparison_reviewed_no_hit_support_pass_count: "
        f"{result.pit_evidence_policy_profile_comparison_reviewed_no_hit_support_pass_count}"
    )
    print(
        "pit_evidence_policy_profile_comparison_no_hit_context_supported_count: "
        f"{result.pit_evidence_policy_profile_comparison_no_hit_context_supported_count}"
    )
    print(
        "pit_evidence_policy_profile_comparison_reviewer_acceptance_required_count: "
        f"{result.pit_evidence_policy_profile_comparison_reviewer_acceptance_required_count}"
    )
    print(
        "pit_evidence_policy_profile_comparison_relaxed_blocker_count: "
        f"{result.pit_evidence_policy_profile_comparison_relaxed_blocker_count}"
    )
    print(
        "pit_evidence_policy_profile_comparison_remaining_blocked_count: "
        f"{result.pit_evidence_policy_profile_comparison_remaining_blocked_count}"
    )
    print(
        "pit_evidence_policy_profile_comparison_report_path: "
        f"{result.pit_evidence_policy_profile_comparison_report_path}"
    )
    print(
        "pit_evidence_policy_profile_comparison_next_action: "
        f"{result.pit_evidence_policy_profile_comparison_next_action}"
    )
    print(
        "latest_pit_official_status_evidence_packet_id: "
        f"{result.latest_pit_official_status_evidence_packet_id}"
    )
    print(
        "pit_official_status_evidence_packet_status: "
        f"{result.pit_official_status_evidence_packet_status}"
    )
    print(
        "pit_official_status_evidence_packet_stage: "
        f"{result.pit_official_status_evidence_packet_stage}"
    )
    print(
        "pit_official_status_evidence_packet_health_status: "
        f"{result.pit_official_status_evidence_packet_health_status}"
    )
    print(
        "pit_official_status_evidence_packet_row_count: "
        f"{result.pit_official_status_evidence_packet_row_count}"
    )
    print(
        "pit_official_status_evidence_packet_evidence_packet_row_count: "
        f"{result.pit_official_status_evidence_packet_evidence_packet_row_count}"
    )
    print(
        "pit_official_status_evidence_packet_strong_official_date_specific_count: "
        f"{result.pit_official_status_evidence_packet_strong_official_date_specific_count}"
    )
    print(
        "pit_official_status_evidence_packet_supporting_official_symbol_level_count: "
        f"{result.pit_official_status_evidence_packet_supporting_official_symbol_level_count}"
    )
    print(
        "pit_official_status_evidence_packet_supporting_local_eod_cache_count: "
        f"{result.pit_official_status_evidence_packet_supporting_local_eod_cache_count}"
    )
    print(
        "pit_official_status_evidence_packet_context_only_count: "
        f"{result.pit_official_status_evidence_packet_context_only_count}"
    )
    print(
        "pit_official_status_evidence_packet_missing_count: "
        f"{result.pit_official_status_evidence_packet_missing_count}"
    )
    print(
        "pit_official_status_evidence_packet_checklist_pass_count: "
        f"{result.pit_official_status_evidence_packet_checklist_pass_count}"
    )
    print(
        "pit_official_status_evidence_packet_blocked_count: "
        f"{result.pit_official_status_evidence_packet_blocked_count}"
    )
    print(
        "pit_official_status_evidence_packet_eod_low_budget_checklist_pass_count: "
        f"{result.pit_official_status_evidence_packet_eod_low_budget_checklist_pass_count}"
    )
    print(
        "pit_official_status_evidence_packet_report_path: "
        f"{result.pit_official_status_evidence_packet_report_path}"
    )
    print(
        "pit_official_status_evidence_packet_next_action: "
        f"{result.pit_official_status_evidence_packet_next_action}"
    )
    print(
        "latest_pit_official_status_evidence_packet_enrichment_id: "
        f"{result.latest_pit_official_status_evidence_packet_enrichment_id}"
    )
    print(
        "pit_official_status_evidence_packet_enrichment_status: "
        f"{result.pit_official_status_evidence_packet_enrichment_status}"
    )
    print(
        "pit_official_status_evidence_packet_enrichment_stage: "
        f"{result.pit_official_status_evidence_packet_enrichment_stage}"
    )
    print(
        "pit_official_status_evidence_packet_enrichment_health_status: "
        f"{result.pit_official_status_evidence_packet_enrichment_health_status}"
    )
    print(
        "pit_official_status_evidence_packet_enrichment_source_packet_id: "
        f"{result.pit_official_status_evidence_packet_enrichment_source_packet_id}"
    )
    print(
        "pit_official_status_evidence_packet_enrichment_policy_comparison_id: "
        f"{result.pit_official_status_evidence_packet_enrichment_policy_comparison_id}"
    )
    print(
        "pit_official_status_evidence_packet_enrichment_row_count: "
        f"{result.pit_official_status_evidence_packet_enrichment_row_count}"
    )
    print(
        "pit_official_status_evidence_packet_enrichment_strong_official_date_specific_quotation_count: "
        f"{result.pit_official_status_evidence_packet_enrichment_strong_official_date_specific_quotation_count}"
    )
    print(
        "pit_official_status_evidence_packet_enrichment_reviewed_no_hit_context_supported_count: "
        f"{result.pit_official_status_evidence_packet_enrichment_reviewed_no_hit_context_supported_count}"
    )
    print(
        "pit_official_status_evidence_packet_enrichment_reviewer_acceptance_required_count: "
        f"{result.pit_official_status_evidence_packet_enrichment_reviewer_acceptance_required_count}"
    )
    print(
        "pit_official_status_evidence_packet_enrichment_checklist_pass_count: "
        f"{result.pit_official_status_evidence_packet_enrichment_checklist_pass_count}"
    )
    print(
        "pit_official_status_evidence_packet_enrichment_remaining_blocked_count: "
        f"{result.pit_official_status_evidence_packet_enrichment_remaining_blocked_count}"
    )
    print(
        "pit_official_status_evidence_packet_enrichment_report_path: "
        f"{result.pit_official_status_evidence_packet_enrichment_report_path}"
    )
    print(
        "pit_official_status_evidence_packet_enrichment_next_action: "
        f"{result.pit_official_status_evidence_packet_enrichment_next_action}"
    )
    print(f"latest_reviewer_no_hit_acceptance_id: {result.latest_reviewer_no_hit_acceptance_id}")
    print(f"reviewer_no_hit_acceptance_status: {result.reviewer_no_hit_acceptance_status}")
    print(f"reviewer_no_hit_acceptance_stage: {result.reviewer_no_hit_acceptance_stage}")
    print(f"reviewer_no_hit_acceptance_health_status: {result.reviewer_no_hit_acceptance_health_status}")
    print(f"reviewer_no_hit_acceptance_enrichment_id: {result.reviewer_no_hit_acceptance_enrichment_id}")
    print(f"reviewer_no_hit_acceptance_source_packet_id: {result.reviewer_no_hit_acceptance_source_packet_id}")
    print(
        "reviewer_no_hit_acceptance_policy_comparison_id: "
        f"{result.reviewer_no_hit_acceptance_policy_comparison_id}"
    )
    print(f"reviewer_no_hit_acceptance_row_count: {result.reviewer_no_hit_acceptance_row_count}")
    print(f"reviewer_no_hit_acceptance_accepted_count: {result.reviewer_no_hit_acceptance_accepted_count}")
    print(f"reviewer_no_hit_acceptance_needs_review_count: {result.reviewer_no_hit_acceptance_needs_review_count}")
    print(
        "reviewer_no_hit_acceptance_needs_more_evidence_count: "
        f"{result.reviewer_no_hit_acceptance_needs_more_evidence_count}"
    )
    print(
        "reviewer_no_hit_acceptance_reviewer_acceptance_required_count: "
        f"{result.reviewer_no_hit_acceptance_reviewer_acceptance_required_count}"
    )
    print(
        "reviewer_no_hit_acceptance_accepted_supporting_context_count: "
        f"{result.reviewer_no_hit_acceptance_accepted_supporting_context_count}"
    )
    print(
        "reviewer_no_hit_acceptance_survivorship_rationale_required_count: "
        f"{result.reviewer_no_hit_acceptance_survivorship_rationale_required_count}"
    )
    print(f"reviewer_no_hit_acceptance_checklist_pass_count: {result.reviewer_no_hit_acceptance_checklist_pass_count}")
    print(f"reviewer_no_hit_acceptance_remaining_blocked_count: {result.reviewer_no_hit_acceptance_remaining_blocked_count}")
    print(f"reviewer_no_hit_acceptance_report_path: {result.reviewer_no_hit_acceptance_report_path}")
    print(f"reviewer_no_hit_acceptance_next_action: {result.reviewer_no_hit_acceptance_next_action}")
    print(
        "latest_reviewer_no_hit_acceptance_downstream_impact_id: "
        f"{result.latest_reviewer_no_hit_acceptance_downstream_impact_id}"
    )
    print(f"reviewer_no_hit_downstream_impact_status: {result.reviewer_no_hit_downstream_impact_status}")
    print(f"reviewer_no_hit_downstream_impact_stage: {result.reviewer_no_hit_downstream_impact_stage}")
    print(
        "reviewer_no_hit_downstream_impact_health_status: "
        f"{result.reviewer_no_hit_downstream_impact_health_status}"
    )
    print(
        "reviewer_no_hit_downstream_impact_accepted_no_hit_context_count: "
        f"{result.reviewer_no_hit_downstream_impact_accepted_no_hit_context_count}"
    )
    print(
        "reviewer_no_hit_downstream_impact_packet_context_gap_reduced_count: "
        f"{result.reviewer_no_hit_downstream_impact_packet_context_gap_reduced_count}"
    )
    print(
        "reviewer_no_hit_downstream_impact_checklist_pass_count: "
        f"{result.reviewer_no_hit_downstream_impact_checklist_pass_count}"
    )
    print(
        "reviewer_no_hit_downstream_impact_remaining_blocked_count: "
        f"{result.reviewer_no_hit_downstream_impact_remaining_blocked_count}"
    )
    print(f"reviewer_no_hit_downstream_impact_approval_applied: {result.reviewer_no_hit_downstream_impact_approval_applied}")
    print(f"reviewer_no_hit_downstream_impact_report_path: {result.reviewer_no_hit_downstream_impact_report_path}")
    print(f"reviewer_no_hit_downstream_impact_next_action: {result.reviewer_no_hit_downstream_impact_next_action}")
    print(
        "latest_first_batch_reviewer_evidence_completion_plan_id: "
        f"{result.latest_first_batch_reviewer_evidence_completion_plan_id}"
    )
    print(
        "first_batch_reviewer_evidence_completion_plan_status: "
        f"{result.first_batch_reviewer_evidence_completion_plan_status}"
    )
    print(
        "first_batch_reviewer_evidence_completion_plan_stage: "
        f"{result.first_batch_reviewer_evidence_completion_plan_stage}"
    )
    print(
        "first_batch_reviewer_evidence_completion_plan_health_status: "
        f"{result.first_batch_reviewer_evidence_completion_plan_health_status}"
    )
    print(
        "first_batch_reviewer_evidence_completion_plan_row_count: "
        f"{result.first_batch_reviewer_evidence_completion_plan_row_count}"
    )
    print(
        "first_batch_reviewer_evidence_completion_plan_reviewer_completion_required_count: "
        f"{result.first_batch_reviewer_evidence_completion_plan_reviewer_completion_required_count}"
    )
    print(
        "first_batch_reviewer_evidence_completion_plan_no_hit_acceptance_required_count: "
        f"{result.first_batch_reviewer_evidence_completion_plan_no_hit_acceptance_required_count}"
    )
    print(
        "first_batch_reviewer_evidence_completion_plan_survivorship_rationale_required_count: "
        f"{result.first_batch_reviewer_evidence_completion_plan_survivorship_rationale_required_count}"
    )
    print(
        "first_batch_reviewer_evidence_completion_plan_metadata_completion_required_count: "
        f"{result.first_batch_reviewer_evidence_completion_plan_metadata_completion_required_count}"
    )
    print(
        "first_batch_reviewer_evidence_completion_plan_checklist_pass_count: "
        f"{result.first_batch_reviewer_evidence_completion_plan_checklist_pass_count}"
    )
    print(
        "first_batch_reviewer_evidence_completion_plan_remaining_blocked_count: "
        f"{result.first_batch_reviewer_evidence_completion_plan_remaining_blocked_count}"
    )
    print(
        "first_batch_reviewer_evidence_completion_plan_clean_review_updates_created: "
        f"{result.first_batch_reviewer_evidence_completion_plan_clean_review_updates_created}"
    )
    print(
        "first_batch_reviewer_evidence_completion_plan_approval_applied: "
        f"{result.first_batch_reviewer_evidence_completion_plan_approval_applied}"
    )
    print(
        "first_batch_reviewer_evidence_completion_plan_report_path: "
        f"{result.first_batch_reviewer_evidence_completion_plan_report_path}"
    )
    print(
        "first_batch_reviewer_evidence_completion_plan_next_action: "
        f"{result.first_batch_reviewer_evidence_completion_plan_next_action}"
    )
    print(
        "latest_first_batch_partial_completion_impact_id: "
        f"{result.latest_first_batch_partial_completion_impact_id}"
    )
    print(
        "first_batch_partial_completion_impact_status: "
        f"{result.first_batch_partial_completion_impact_status}"
    )
    print(
        "first_batch_partial_completion_impact_stage: "
        f"{result.first_batch_partial_completion_impact_stage}"
    )
    print(
        "first_batch_partial_completion_impact_health_status: "
        f"{result.first_batch_partial_completion_impact_health_status}"
    )
    print(
        "first_batch_partial_completion_impact_completed_row_count: "
        f"{result.first_batch_partial_completion_impact_completed_row_count}"
    )
    print(
        "first_batch_partial_completion_impact_completed_field_count: "
        f"{result.first_batch_partial_completion_impact_completed_field_count}"
    )
    print(
        "first_batch_partial_completion_impact_blocker_reduced_count: "
        f"{result.first_batch_partial_completion_impact_blocker_reduced_count}"
    )
    print(
        "first_batch_partial_completion_impact_material_blocker_reduced_count: "
        f"{result.first_batch_partial_completion_impact_material_blocker_reduced_count}"
    )
    print(
        "first_batch_partial_completion_impact_checklist_pass_count: "
        f"{result.first_batch_partial_completion_impact_checklist_pass_count}"
    )
    print(
        "first_batch_partial_completion_impact_remaining_blocked_count: "
        f"{result.first_batch_partial_completion_impact_remaining_blocked_count}"
    )
    print(
        "first_batch_partial_completion_impact_clean_review_updates_created: "
        f"{result.first_batch_partial_completion_impact_clean_review_updates_created}"
    )
    print(
        "first_batch_partial_completion_impact_approval_applied: "
        f"{result.first_batch_partial_completion_impact_approval_applied}"
    )
    print(
        "first_batch_partial_completion_impact_report_path: "
        f"{result.first_batch_partial_completion_impact_report_path}"
    )
    print(
        "first_batch_partial_completion_impact_next_action: "
        f"{result.first_batch_partial_completion_impact_next_action}"
    )
    print(
        "latest_material_pit_evidence_gate_closure_plan_id: "
        f"{result.latest_material_pit_evidence_gate_closure_plan_id}"
    )
    print(
        "material_pit_evidence_gate_closure_plan_status: "
        f"{result.material_pit_evidence_gate_closure_plan_status}"
    )
    print(
        "material_pit_evidence_gate_closure_plan_stage: "
        f"{result.material_pit_evidence_gate_closure_plan_stage}"
    )
    print(
        "material_pit_evidence_gate_closure_plan_health_status: "
        f"{result.material_pit_evidence_gate_closure_plan_health_status}"
    )
    print(
        "material_pit_evidence_gate_closure_plan_row_count: "
        f"{result.material_pit_evidence_gate_closure_plan_row_count}"
    )
    print(
        "material_pit_evidence_gate_closure_plan_checklist_pass_candidate_count: "
        f"{result.material_pit_evidence_gate_closure_plan_checklist_pass_candidate_count}"
    )
    print(
        "material_pit_evidence_gate_closure_plan_remaining_blocked_count: "
        f"{result.material_pit_evidence_gate_closure_plan_remaining_blocked_count}"
    )
    print(
        "material_pit_evidence_gate_closure_plan_reusable_symbol_level_closure_count: "
        f"{result.material_pit_evidence_gate_closure_plan_reusable_symbol_level_closure_count}"
    )
    print(
        "material_pit_evidence_gate_closure_plan_date_specific_closure_required_count: "
        f"{result.material_pit_evidence_gate_closure_plan_date_specific_closure_required_count}"
    )
    print(
        "material_pit_evidence_gate_closure_plan_reviewer_no_hit_acceptance_required_count: "
        f"{result.material_pit_evidence_gate_closure_plan_reviewer_no_hit_acceptance_required_count}"
    )
    print(
        "material_pit_evidence_gate_closure_plan_survivorship_rationale_required_count: "
        f"{result.material_pit_evidence_gate_closure_plan_survivorship_rationale_required_count}"
    )
    print(
        "material_pit_evidence_gate_closure_plan_metadata_closure_required_count: "
        f"{result.material_pit_evidence_gate_closure_plan_metadata_closure_required_count}"
    )
    print(
        "material_pit_evidence_gate_closure_plan_stock_st_no_st_required_count: "
        f"{result.material_pit_evidence_gate_closure_plan_stock_st_no_st_required_count}"
    )
    print(
        "material_pit_evidence_gate_closure_plan_clean_review_updates_created: "
        f"{result.material_pit_evidence_gate_closure_plan_clean_review_updates_created}"
    )
    print(
        "material_pit_evidence_gate_closure_plan_approval_applied: "
        f"{result.material_pit_evidence_gate_closure_plan_approval_applied}"
    )
    print(
        "material_pit_evidence_gate_closure_plan_report_path: "
        f"{result.material_pit_evidence_gate_closure_plan_report_path}"
    )
    print(
        "material_pit_evidence_gate_closure_plan_next_action: "
        f"{result.material_pit_evidence_gate_closure_plan_next_action}"
    )
    print(
        "latest_reviewer_material_evidence_fill_guidance_id: "
        f"{result.latest_reviewer_material_evidence_fill_guidance_id}"
    )
    print(
        "reviewer_material_evidence_fill_guidance_status: "
        f"{result.reviewer_material_evidence_fill_guidance_status}"
    )
    print(
        "reviewer_material_evidence_fill_guidance_stage: "
        f"{result.reviewer_material_evidence_fill_guidance_stage}"
    )
    print(
        "reviewer_material_evidence_fill_guidance_health_status: "
        f"{result.reviewer_material_evidence_fill_guidance_health_status}"
    )
    print(
        "reviewer_material_evidence_fill_guidance_row_count: "
        f"{result.reviewer_material_evidence_fill_guidance_row_count}"
    )
    print(
        "reviewer_material_evidence_fill_guidance_reviewer_guidance_row_count: "
        f"{result.reviewer_material_evidence_fill_guidance_reviewer_guidance_row_count}"
    )
    print(
        "reviewer_material_evidence_fill_guidance_symbol_level_guidance_count: "
        f"{result.reviewer_material_evidence_fill_guidance_symbol_level_guidance_count}"
    )
    print(
        "reviewer_material_evidence_fill_guidance_date_specific_guidance_count: "
        f"{result.reviewer_material_evidence_fill_guidance_date_specific_guidance_count}"
    )
    print(
        "reviewer_material_evidence_fill_guidance_no_hit_acceptance_guidance_count: "
        f"{result.reviewer_material_evidence_fill_guidance_no_hit_acceptance_guidance_count}"
    )
    print(
        "reviewer_material_evidence_fill_guidance_survivorship_rationale_guidance_count: "
        f"{result.reviewer_material_evidence_fill_guidance_survivorship_rationale_guidance_count}"
    )
    print(
        "reviewer_material_evidence_fill_guidance_metadata_guidance_count: "
        f"{result.reviewer_material_evidence_fill_guidance_metadata_guidance_count}"
    )
    print(
        "reviewer_material_evidence_fill_guidance_checklist_pass_candidate_count: "
        f"{result.reviewer_material_evidence_fill_guidance_checklist_pass_candidate_count}"
    )
    print(
        "reviewer_material_evidence_fill_guidance_remaining_blocked_count: "
        f"{result.reviewer_material_evidence_fill_guidance_remaining_blocked_count}"
    )
    print(
        "reviewer_material_evidence_fill_guidance_clean_review_updates_created: "
        f"{result.reviewer_material_evidence_fill_guidance_clean_review_updates_created}"
    )
    print(
        "reviewer_material_evidence_fill_guidance_approval_applied: "
        f"{result.reviewer_material_evidence_fill_guidance_approval_applied}"
    )
    print(
        "reviewer_material_evidence_fill_guidance_report_path: "
        f"{result.reviewer_material_evidence_fill_guidance_report_path}"
    )
    print(
        "reviewer_material_evidence_fill_guidance_next_action: "
        f"{result.reviewer_material_evidence_fill_guidance_next_action}"
    )
    print(
        "latest_one_row_material_evidence_fill_package_id: "
        f"{result.latest_one_row_material_evidence_fill_package_id}"
    )
    print(
        "one_row_material_evidence_fill_package_status: "
        f"{result.one_row_material_evidence_fill_package_status}"
    )
    print(
        "one_row_material_evidence_fill_package_stage: "
        f"{result.one_row_material_evidence_fill_package_stage}"
    )
    print(
        "one_row_material_evidence_fill_package_health_status: "
        f"{result.one_row_material_evidence_fill_package_health_status}"
    )
    print(
        "one_row_material_evidence_fill_package_target_signal_date: "
        f"{result.one_row_material_evidence_fill_package_target_signal_date}"
    )
    print(
        "one_row_material_evidence_fill_package_target_symbol: "
        f"{result.one_row_material_evidence_fill_package_target_symbol}"
    )
    print(
        "one_row_material_evidence_fill_package_target_universe_name: "
        f"{result.one_row_material_evidence_fill_package_target_universe_name}"
    )
    print(
        "one_row_material_evidence_fill_package_package_row_count: "
        f"{result.one_row_material_evidence_fill_package_package_row_count}"
    )
    print(
        "one_row_material_evidence_fill_package_context_field_drafted_count: "
        f"{result.one_row_material_evidence_fill_package_context_field_drafted_count}"
    )
    print(
        "one_row_material_evidence_fill_package_material_blocker_closed_count: "
        f"{result.one_row_material_evidence_fill_package_material_blocker_closed_count}"
    )
    print(
        "one_row_material_evidence_fill_package_checklist_pass_candidate_count: "
        f"{result.one_row_material_evidence_fill_package_checklist_pass_candidate_count}"
    )
    print(
        "one_row_material_evidence_fill_package_remaining_blocked_count: "
        f"{result.one_row_material_evidence_fill_package_remaining_blocked_count}"
    )
    print(
        "one_row_material_evidence_fill_package_clean_review_updates_created: "
        f"{result.one_row_material_evidence_fill_package_clean_review_updates_created}"
    )
    print(
        "one_row_material_evidence_fill_package_approval_applied: "
        f"{result.one_row_material_evidence_fill_package_approval_applied}"
    )
    print(
        "one_row_material_evidence_fill_package_report_path: "
        f"{result.one_row_material_evidence_fill_package_report_path}"
    )
    print(
        "one_row_material_evidence_fill_package_next_action: "
        f"{result.one_row_material_evidence_fill_package_next_action}"
    )
    print(
        "latest_one_row_checklist_pass_candidate_preview_id: "
        f"{result.latest_one_row_checklist_pass_candidate_preview_id}"
    )
    print(
        "one_row_checklist_pass_candidate_preview_status: "
        f"{result.one_row_checklist_pass_candidate_preview_status}"
    )
    print(
        "one_row_checklist_pass_candidate_preview_stage: "
        f"{result.one_row_checklist_pass_candidate_preview_stage}"
    )
    print(
        "one_row_checklist_pass_candidate_preview_health_status: "
        f"{result.one_row_checklist_pass_candidate_preview_health_status}"
    )
    print(
        "one_row_checklist_pass_candidate_preview_target_signal_date: "
        f"{result.one_row_checklist_pass_candidate_preview_target_signal_date}"
    )
    print(
        "one_row_checklist_pass_candidate_preview_target_symbol: "
        f"{result.one_row_checklist_pass_candidate_preview_target_symbol}"
    )
    print(
        "one_row_checklist_pass_candidate_preview_target_universe_name: "
        f"{result.one_row_checklist_pass_candidate_preview_target_universe_name}"
    )
    print(
        "one_row_checklist_pass_candidate_preview_preview_row_count: "
        f"{result.one_row_checklist_pass_candidate_preview_preview_row_count}"
    )
    print(
        "one_row_checklist_pass_candidate_preview_reusable_context_field_count: "
        f"{result.one_row_checklist_pass_candidate_preview_reusable_context_field_count}"
    )
    print(
        "one_row_checklist_pass_candidate_preview_strict_requirement_gap_count: "
        f"{result.one_row_checklist_pass_candidate_preview_strict_requirement_gap_count}"
    )
    print(
        "one_row_checklist_pass_candidate_preview_row_checklist_pass_candidate: "
        f"{result.one_row_checklist_pass_candidate_preview_row_checklist_pass_candidate}"
    )
    print(
        "one_row_checklist_pass_candidate_preview_checklist_pass_candidate_count: "
        f"{result.one_row_checklist_pass_candidate_preview_checklist_pass_candidate_count}"
    )
    print(
        "one_row_checklist_pass_candidate_preview_remaining_blocked_count: "
        f"{result.one_row_checklist_pass_candidate_preview_remaining_blocked_count}"
    )
    print(
        "one_row_checklist_pass_candidate_preview_clean_review_updates_created: "
        f"{result.one_row_checklist_pass_candidate_preview_clean_review_updates_created}"
    )
    print(
        "one_row_checklist_pass_candidate_preview_approval_applied: "
        f"{result.one_row_checklist_pass_candidate_preview_approval_applied}"
    )
    print(
        "one_row_checklist_pass_candidate_preview_report_path: "
        f"{result.one_row_checklist_pass_candidate_preview_report_path}"
    )
    print(
        "one_row_checklist_pass_candidate_preview_next_action: "
        f"{result.one_row_checklist_pass_candidate_preview_next_action}"
    )
    print(
        "latest_replay_substrate_schema_fixture_id: "
        f"{result.latest_replay_substrate_schema_fixture_id}"
    )
    print(f"replay_substrate_schema_fixture_status: {result.replay_substrate_schema_fixture_status}")
    print(f"replay_substrate_schema_fixture_stage: {result.replay_substrate_schema_fixture_stage}")
    print(
        "replay_substrate_schema_fixture_health_status: "
        f"{result.replay_substrate_schema_fixture_health_status}"
    )
    print(
        "replay_substrate_schema_fixture_entity_count: "
        f"{result.replay_substrate_schema_fixture_entity_count}"
    )
    print(
        "replay_substrate_schema_fixture_validation_issue_count: "
        f"{result.replay_substrate_schema_fixture_validation_issue_count}"
    )
    print(
        "replay_substrate_schema_fixture_overclaim_guard_status: "
        f"{result.replay_substrate_schema_fixture_overclaim_guard_status}"
    )
    print(
        "replay_substrate_schema_fixture_overclaim_guard_pass_count: "
        f"{result.replay_substrate_schema_fixture_overclaim_guard_pass_count}"
    )
    print(
        "replay_substrate_schema_fixture_overclaim_guard_total_count: "
        f"{result.replay_substrate_schema_fixture_overclaim_guard_total_count}"
    )
    print(
        "replay_substrate_schema_fixture_active_replay_input: "
        f"{result.replay_substrate_schema_fixture_active_replay_input}"
    )
    print(
        "replay_substrate_schema_fixture_forward_labels_exist: "
        f"{result.replay_substrate_schema_fixture_forward_labels_exist}"
    )
    print(
        "replay_substrate_schema_fixture_weights_trained: "
        f"{result.replay_substrate_schema_fixture_weights_trained}"
    )
    print(
        "replay_substrate_schema_fixture_active_stock_profile_exists: "
        f"{result.replay_substrate_schema_fixture_active_stock_profile_exists}"
    )
    print(
        "replay_substrate_schema_fixture_real_buy_review_eligible: "
        f"{result.replay_substrate_schema_fixture_real_buy_review_eligible}"
    )
    print(f"replay_substrate_schema_fixture_report_only: {result.replay_substrate_schema_fixture_report_only}")
    print(f"replay_substrate_schema_fixture_diagnostic_only: {result.replay_substrate_schema_fixture_diagnostic_only}")
    print(f"replay_substrate_schema_fixture_no_live_trading: {result.replay_substrate_schema_fixture_no_live_trading}")
    print(f"replay_substrate_schema_fixture_no_broker_api: {result.replay_substrate_schema_fixture_no_broker_api}")
    print(
        "replay_substrate_schema_fixture_no_order_placement: "
        f"{result.replay_substrate_schema_fixture_no_order_placement}"
    )
    print(f"replay_substrate_schema_fixture_report_path: {result.replay_substrate_schema_fixture_report_path}")
    print(f"replay_substrate_schema_fixture_next_action: {result.replay_substrate_schema_fixture_next_action}")
    print(
        "latest_input_gate_validator_fixture_run_id: "
        f"{result.latest_input_gate_validator_fixture_run_id}"
    )
    print(f"input_gate_validator_fixture_status: {result.input_gate_validator_fixture_status}")
    print(f"input_gate_validator_fixture_stage: {result.input_gate_validator_fixture_stage}")
    print(
        "input_gate_validator_fixture_health_status: "
        f"{result.input_gate_validator_fixture_health_status}"
    )
    print(f"input_gate_validator_fixture_case_count: {result.input_gate_validator_fixture_case_count}")
    print(
        "input_gate_validator_fixture_blocked_case_count: "
        f"{result.input_gate_validator_fixture_blocked_case_count}"
    )
    print(
        "input_gate_validator_fixture_pass_candidate_case_count: "
        f"{result.input_gate_validator_fixture_pass_candidate_case_count}"
    )
    print(
        "input_gate_validator_fixture_active_ready_case_count: "
        f"{result.input_gate_validator_fixture_active_ready_case_count}"
    )
    print(
        "input_gate_validator_fixture_validation_issue_count: "
        f"{result.input_gate_validator_fixture_validation_issue_count}"
    )
    print(
        "input_gate_validator_fixture_overclaim_guard_pass_count: "
        f"{result.input_gate_validator_fixture_overclaim_guard_pass_count}"
    )
    print(
        "input_gate_validator_fixture_overclaim_guard_total_count: "
        f"{result.input_gate_validator_fixture_overclaim_guard_total_count}"
    )
    print(
        "input_gate_validator_fixture_active_replay_input: "
        f"{result.input_gate_validator_fixture_active_replay_input}"
    )
    print(
        "input_gate_validator_fixture_forward_labels_exist: "
        f"{result.input_gate_validator_fixture_forward_labels_exist}"
    )
    print(
        "input_gate_validator_fixture_weights_trained: "
        f"{result.input_gate_validator_fixture_weights_trained}"
    )
    print(
        "input_gate_validator_fixture_active_stock_profile_exists: "
        f"{result.input_gate_validator_fixture_active_stock_profile_exists}"
    )
    print(
        "input_gate_validator_fixture_real_buy_review_eligible: "
        f"{result.input_gate_validator_fixture_real_buy_review_eligible}"
    )
    print(
        "input_gate_validator_fixture_validator_implemented: "
        f"{result.input_gate_validator_fixture_validator_implemented}"
    )
    print(f"input_gate_validator_fixture_report_only: {result.input_gate_validator_fixture_report_only}")
    print(f"input_gate_validator_fixture_diagnostic_only: {result.input_gate_validator_fixture_diagnostic_only}")
    print(f"input_gate_validator_fixture_no_live_trading: {result.input_gate_validator_fixture_no_live_trading}")
    print(f"input_gate_validator_fixture_no_broker_api: {result.input_gate_validator_fixture_no_broker_api}")
    print(
        "input_gate_validator_fixture_no_order_placement: "
        f"{result.input_gate_validator_fixture_no_order_placement}"
    )
    print(f"input_gate_validator_fixture_no_message_sent: {result.input_gate_validator_fixture_no_message_sent}")
    print(f"input_gate_validator_fixture_llm_api_called: {result.input_gate_validator_fixture_llm_api_called}")
    print(
        "input_gate_validator_fixture_external_api_called: "
        f"{result.input_gate_validator_fixture_external_api_called}"
    )
    print(f"input_gate_validator_fixture_cache_mutated: {result.input_gate_validator_fixture_cache_mutated}")
    print(
        "input_gate_validator_fixture_current_candidates_run: "
        f"{result.input_gate_validator_fixture_current_candidates_run}"
    )
    print(f"input_gate_validator_fixture_snapshot_built: {result.input_gate_validator_fixture_snapshot_built}")
    print(
        "input_gate_validator_fixture_signal_semantics_changed: "
        f"{result.input_gate_validator_fixture_signal_semantics_changed}"
    )
    print(f"input_gate_validator_fixture_report_path: {result.input_gate_validator_fixture_report_path}")
    print(f"input_gate_validator_fixture_next_action: {result.input_gate_validator_fixture_next_action}")
    print(f"latest_universe_profile_policy_audit_id: {result.latest_universe_profile_policy_audit_id}")
    print(f"universe_profile_policy_audit_status: {result.universe_profile_policy_audit_status}")
    print(f"universe_profile_policy_audit_stage: {result.universe_profile_policy_audit_stage}")
    print(f"universe_profile_policy_audit_health_status: {result.universe_profile_policy_audit_health_status}")
    print(f"universe_profile_policy_row_count: {result.universe_profile_policy_row_count}")
    print(f"universe_profile_policy_stock_row_count: {result.universe_profile_policy_stock_row_count}")
    print(f"universe_profile_policy_etf_row_count: {result.universe_profile_policy_etf_row_count}")
    print(f"universe_profile_policy_mixed_universe_count: {result.universe_profile_policy_mixed_universe_count}")
    print(f"universe_profile_policy_ambiguous_policy_count: {result.universe_profile_policy_ambiguous_policy_count}")
    print(
        "universe_profile_policy_recommended_stock_core_count: "
        f"{result.universe_profile_policy_recommended_stock_core_count}"
    )
    print(
        "universe_profile_policy_recommended_etf_core_count: "
        f"{result.universe_profile_policy_recommended_etf_core_count}"
    )
    print(
        "universe_profile_policy_recommended_mixed_demo_core_count: "
        f"{result.universe_profile_policy_recommended_mixed_demo_core_count}"
    )
    print(f"universe_profile_policy_report_path: {result.universe_profile_policy_report_path}")
    print(f"universe_profile_policy_next_action: {result.universe_profile_policy_next_action}")
    print(
        "latest_universe_profile_split_worklist_plan_id: "
        f"{result.latest_universe_profile_split_worklist_plan_id}"
    )
    print(
        "universe_profile_split_worklist_plan_status: "
        f"{result.universe_profile_split_worklist_plan_status}"
    )
    print(
        "universe_profile_split_worklist_plan_stage: "
        f"{result.universe_profile_split_worklist_plan_stage}"
    )
    print(
        "universe_profile_split_worklist_plan_health_status: "
        f"{result.universe_profile_split_worklist_plan_health_status}"
    )
    print(
        "universe_profile_split_worklist_plan_row_count: "
        f"{result.universe_profile_split_worklist_plan_row_count}"
    )
    print(
        "universe_profile_split_worklist_plan_stock_row_count: "
        f"{result.universe_profile_split_worklist_plan_stock_row_count}"
    )
    print(
        "universe_profile_split_worklist_plan_etf_row_count: "
        f"{result.universe_profile_split_worklist_plan_etf_row_count}"
    )
    print(
        "universe_profile_split_worklist_plan_legacy_mixed_demo_row_count: "
        f"{result.universe_profile_split_worklist_plan_legacy_mixed_demo_row_count}"
    )
    print(
        "universe_profile_split_worklist_plan_recommended_stock_core_count: "
        f"{result.universe_profile_split_worklist_plan_recommended_stock_core_count}"
    )
    print(
        "universe_profile_split_worklist_plan_recommended_etf_core_count: "
        f"{result.universe_profile_split_worklist_plan_recommended_etf_core_count}"
    )
    print(
        "universe_profile_split_worklist_plan_recommended_mixed_demo_core_count: "
        f"{result.universe_profile_split_worklist_plan_recommended_mixed_demo_core_count}"
    )
    print(
        "universe_profile_split_worklist_plan_profile_conflict_count: "
        f"{result.universe_profile_split_worklist_plan_profile_conflict_count}"
    )
    print(
        "universe_profile_split_worklist_plan_report_path: "
        f"{result.universe_profile_split_worklist_plan_report_path}"
    )
    print(
        "universe_profile_split_worklist_plan_next_action: "
        f"{result.universe_profile_split_worklist_plan_next_action}"
    )
    print(f"latest_reviewed_replacement_worklist_plan_id: {result.latest_reviewed_replacement_worklist_plan_id}")
    print(f"reviewed_replacement_worklist_plan_status: {result.reviewed_replacement_worklist_plan_status}")
    print(f"reviewed_replacement_worklist_plan_stage: {result.reviewed_replacement_worklist_plan_stage}")
    print(
        "reviewed_replacement_worklist_plan_health_status: "
        f"{result.reviewed_replacement_worklist_plan_health_status}"
    )
    print(
        "reviewed_replacement_worklist_plan_source_split_plan_id: "
        f"{result.reviewed_replacement_worklist_plan_source_split_plan_id}"
    )
    print(f"reviewed_replacement_worklist_plan_row_count: {result.reviewed_replacement_worklist_plan_row_count}")
    print(
        "reviewed_replacement_worklist_plan_stock_core_row_count: "
        f"{result.reviewed_replacement_worklist_plan_stock_core_row_count}"
    )
    print(
        "reviewed_replacement_worklist_plan_etf_core_row_count: "
        f"{result.reviewed_replacement_worklist_plan_etf_core_row_count}"
    )
    print(
        "reviewed_replacement_worklist_plan_mixed_demo_core_row_count: "
        f"{result.reviewed_replacement_worklist_plan_mixed_demo_core_row_count}"
    )
    print(
        "reviewed_replacement_worklist_plan_profile_conflict_count: "
        f"{result.reviewed_replacement_worklist_plan_profile_conflict_count}"
    )
    print(
        "reviewed_replacement_worklist_plan_active_worklist_mutated: "
        f"{result.reviewed_replacement_worklist_plan_active_worklist_mutated}"
    )
    print(f"reviewed_replacement_worklist_plan_report_path: {result.reviewed_replacement_worklist_plan_report_path}")
    print(f"reviewed_replacement_worklist_plan_next_action: {result.reviewed_replacement_worklist_plan_next_action}")
    print(
        "latest_reviewed_replacement_worklist_acceptance_id: "
        f"{result.latest_reviewed_replacement_worklist_acceptance_id}"
    )
    print(
        "reviewed_replacement_worklist_acceptance_status: "
        f"{result.reviewed_replacement_worklist_acceptance_status}"
    )
    print(
        "reviewed_replacement_worklist_acceptance_stage: "
        f"{result.reviewed_replacement_worklist_acceptance_stage}"
    )
    print(
        "reviewed_replacement_worklist_acceptance_health_status: "
        f"{result.reviewed_replacement_worklist_acceptance_health_status}"
    )
    print(
        "reviewed_replacement_worklist_acceptance_replacement_plan_id: "
        f"{result.reviewed_replacement_worklist_acceptance_replacement_plan_id}"
    )
    print(
        "reviewed_replacement_worklist_acceptance_source_split_plan_id: "
        f"{result.reviewed_replacement_worklist_acceptance_source_split_plan_id}"
    )
    print(
        "reviewed_replacement_worklist_acceptance_source_policy_audit_id: "
        f"{result.reviewed_replacement_worklist_acceptance_source_policy_audit_id}"
    )
    print(
        "reviewed_replacement_worklist_acceptance_source_worklist_id: "
        f"{result.reviewed_replacement_worklist_acceptance_source_worklist_id}"
    )
    print(
        "reviewed_replacement_worklist_acceptance_row_count: "
        f"{result.reviewed_replacement_worklist_acceptance_row_count}"
    )
    print(
        "reviewed_replacement_worklist_acceptance_stock_core_row_count: "
        f"{result.reviewed_replacement_worklist_acceptance_stock_core_row_count}"
    )
    print(
        "reviewed_replacement_worklist_acceptance_etf_core_row_count: "
        f"{result.reviewed_replacement_worklist_acceptance_etf_core_row_count}"
    )
    print(
        "reviewed_replacement_worklist_acceptance_mixed_demo_core_row_count: "
        f"{result.reviewed_replacement_worklist_acceptance_mixed_demo_core_row_count}"
    )
    print(
        "reviewed_replacement_worklist_acceptance_acceptance_acknowledged: "
        f"{result.reviewed_replacement_worklist_acceptance_acceptance_acknowledged}"
    )
    print(
        "reviewed_replacement_worklist_acceptance_active_worklist_mutated: "
        f"{result.reviewed_replacement_worklist_acceptance_active_worklist_mutated}"
    )
    print(
        "reviewed_replacement_worklist_acceptance_report_path: "
        f"{result.reviewed_replacement_worklist_acceptance_report_path}"
    )
    print(
        "reviewed_replacement_worklist_acceptance_next_action: "
        f"{result.reviewed_replacement_worklist_acceptance_next_action}"
    )
    print(
        "latest_reviewed_replacement_worklist_activation_id: "
        f"{result.latest_reviewed_replacement_worklist_activation_id}"
    )
    print(
        "reviewed_replacement_worklist_activation_status: "
        f"{result.reviewed_replacement_worklist_activation_status}"
    )
    print(
        "reviewed_replacement_worklist_activation_stage: "
        f"{result.reviewed_replacement_worklist_activation_stage}"
    )
    print(
        "reviewed_replacement_worklist_activation_health_status: "
        f"{result.reviewed_replacement_worklist_activation_health_status}"
    )
    print(
        "reviewed_replacement_worklist_activation_replacement_plan_id: "
        f"{result.reviewed_replacement_worklist_activation_replacement_plan_id}"
    )
    print(
        "reviewed_replacement_worklist_activation_source_split_plan_id: "
        f"{result.reviewed_replacement_worklist_activation_source_split_plan_id}"
    )
    print(
        "reviewed_replacement_worklist_activation_source_policy_audit_id: "
        f"{result.reviewed_replacement_worklist_activation_source_policy_audit_id}"
    )
    print(
        "reviewed_replacement_worklist_activation_source_worklist_id: "
        f"{result.reviewed_replacement_worklist_activation_source_worklist_id}"
    )
    print(
        "reviewed_replacement_worklist_activation_row_count: "
        f"{result.reviewed_replacement_worklist_activation_row_count}"
    )
    print(
        "reviewed_replacement_worklist_activation_stock_core_row_count: "
        f"{result.reviewed_replacement_worklist_activation_stock_core_row_count}"
    )
    print(
        "reviewed_replacement_worklist_activation_etf_core_row_count: "
        f"{result.reviewed_replacement_worklist_activation_etf_core_row_count}"
    )
    print(
        "reviewed_replacement_worklist_activation_mixed_demo_core_row_count: "
        f"{result.reviewed_replacement_worklist_activation_mixed_demo_core_row_count}"
    )
    print(
        "reviewed_replacement_worklist_activation_activation_acknowledged: "
        f"{result.reviewed_replacement_worklist_activation_activation_acknowledged}"
    )
    print(
        "reviewed_replacement_worklist_activation_active_worklist_mutated: "
        f"{result.reviewed_replacement_worklist_activation_active_worklist_mutated}"
    )
    print(
        "reviewed_replacement_worklist_activation_report_path: "
        f"{result.reviewed_replacement_worklist_activation_report_path}"
    )
    print(
        "reviewed_replacement_worklist_activation_next_action: "
        f"{result.reviewed_replacement_worklist_activation_next_action}"
    )
    print(
        "latest_activated_replacement_worklist_evidence_update_plan_id: "
        f"{result.latest_activated_replacement_worklist_evidence_update_plan_id}"
    )
    print(
        "activated_replacement_worklist_evidence_update_plan_status: "
        f"{result.activated_replacement_worklist_evidence_update_plan_status}"
    )
    print(
        "activated_replacement_worklist_evidence_update_plan_stage: "
        f"{result.activated_replacement_worklist_evidence_update_plan_stage}"
    )
    print(
        "activated_replacement_worklist_evidence_update_plan_health_status: "
        f"{result.activated_replacement_worklist_evidence_update_plan_health_status}"
    )
    print(
        "activated_replacement_worklist_evidence_update_plan_stock_core_row_count: "
        f"{result.activated_replacement_worklist_evidence_update_plan_stock_core_row_count}"
    )
    print(
        "activated_replacement_worklist_evidence_update_plan_etf_core_row_count: "
        f"{result.activated_replacement_worklist_evidence_update_plan_etf_core_row_count}"
    )
    print(
        "activated_replacement_worklist_evidence_update_plan_valid_for_signal_date_count: "
        f"{result.activated_replacement_worklist_evidence_update_plan_valid_for_signal_date_count}"
    )
    print(
        "activated_replacement_worklist_evidence_update_plan_clean_review_updates_created: "
        f"{result.activated_replacement_worklist_evidence_update_plan_clean_review_updates_created}"
    )
    print(
        "activated_replacement_worklist_evidence_update_plan_next_action: "
        f"{result.activated_replacement_worklist_evidence_update_plan_next_action}"
    )
    print(f"latest_advisory_profile_calibration_run_id: {result.latest_advisory_profile_calibration_run_id}")
    print(f"advisory_profile_calibration_status: {result.advisory_profile_calibration_status}")
    print(f"advisory_profile_calibration_stage: {result.advisory_profile_calibration_stage}")
    print(f"advisory_profile_calibration_profile: {result.advisory_profile_calibration_profile}")
    print(f"advisory_profile_calibration_health_status: {result.advisory_profile_calibration_health_status}")
    print(
        "advisory_profile_calibration_review_buy_candidate_count: "
        f"{result.advisory_profile_calibration_review_buy_candidate_count}"
    )
    print(f"advisory_profile_calibration_watch_count: {result.advisory_profile_calibration_watch_count}")
    print(f"advisory_profile_calibration_no_action_count: {result.advisory_profile_calibration_no_action_count}")
    print(f"advisory_profile_calibration_blocked_count: {result.advisory_profile_calibration_blocked_count}")
    print(f"advisory_profile_calibration_demo_only_count: {result.advisory_profile_calibration_demo_only_count}")
    print(f"advisory_profile_calibration_issue_count: {result.advisory_profile_calibration_issue_count}")
    print(f"advisory_profile_calibration_report_path: {result.advisory_profile_calibration_report_path}")
    print(f"advisory_profile_calibration_next_action: {result.advisory_profile_calibration_next_action}")
    print(
        "latest_calibration_to_signal_semantics_proposal_run_id: "
        f"{result.latest_calibration_to_signal_semantics_proposal_run_id}"
    )
    print(f"calibration_to_signal_semantics_status: {result.calibration_to_signal_semantics_status}")
    print(f"calibration_to_signal_semantics_stage: {result.calibration_to_signal_semantics_stage}")
    print(
        "calibration_to_signal_semantics_health_status: "
        f"{result.calibration_to_signal_semantics_health_status}"
    )
    print(
        "calibration_to_signal_semantics_defaults_changed: "
        f"{result.calibration_to_signal_semantics_defaults_changed}"
    )
    print(
        "calibration_to_signal_semantics_proposal_categories: "
        f"{result.calibration_to_signal_semantics_proposal_categories}"
    )
    print(
        "calibration_to_signal_semantics_calibration_run_count: "
        f"{result.calibration_to_signal_semantics_calibration_run_count}"
    )
    print(
        "calibration_to_signal_semantics_observed_review_buy_candidate_count: "
        f"{result.calibration_to_signal_semantics_observed_review_buy_candidate_count}"
    )
    print(
        "calibration_to_signal_semantics_observed_watch_count: "
        f"{result.calibration_to_signal_semantics_observed_watch_count}"
    )
    print(
        "calibration_to_signal_semantics_observed_blocked_count: "
        f"{result.calibration_to_signal_semantics_observed_blocked_count}"
    )
    print(f"calibration_to_signal_semantics_report_path: {result.calibration_to_signal_semantics_report_path}")
    print(f"calibration_to_signal_semantics_next_action: {result.calibration_to_signal_semantics_next_action}")
    print(f"latest_signal_semantics_run_id: {result.latest_signal_semantics_run_id}")
    print(f"signal_semantics_status: {result.signal_semantics_status}")
    print(f"signal_semantics_stage: {result.signal_semantics_stage}")
    print(f"signal_semantics_health_status: {result.signal_semantics_health_status}")
    print(f"signal_semantics_demo_only_count: {result.signal_semantics_demo_only_count}")
    print(f"signal_semantics_watch_count: {result.signal_semantics_watch_count}")
    print(f"signal_semantics_review_buy_candidate_count: {result.signal_semantics_review_buy_candidate_count}")
    print(f"signal_semantics_review_sell_candidate_count: {result.signal_semantics_review_sell_candidate_count}")
    print(f"signal_semantics_hold_review_count: {result.signal_semantics_hold_review_count}")
    print(f"signal_semantics_no_action_count: {result.signal_semantics_no_action_count}")
    print(f"signal_semantics_blocked_count: {result.signal_semantics_blocked_count}")
    print(f"signal_semantics_issue_count: {result.signal_semantics_issue_count}")
    print(f"signal_semantics_profile: {result.signal_semantics_profile}")
    print(f"signal_semantics_input_path: {result.signal_semantics_input_path}")
    print(f"signal_semantics_report_path: {result.signal_semantics_report_path}")
    print(f"signal_semantics_next_action: {result.signal_semantics_next_action}")
    print(f"latest_signal_run_id: {result.latest_signal_run_id}")
    print(f"signal_advisory_status: {result.signal_advisory_status}")
    print(f"signal_advisory_stage: {result.signal_advisory_stage}")
    print(f"signal_advisory_next_action: {result.signal_advisory_next_action}")
    print(f"signal_health_status: {result.signal_health_status}")
    print(f"signal_count: {result.signal_count}")
    print(f"demo_signal_count: {result.demo_signal_count}")
    print(f"advisory_action_counts: {result.advisory_action_counts}")
    print(f"alert_preview_path: {result.alert_preview_path}")
    print(f"source_candidate_run_id: {result.source_candidate_run_id}")
    print(f"selection_profile: {result.selection_profile}")
    print(f"demo_mode: {result.demo_mode}")
    print(f"not_strategy_recommendation: {result.not_strategy_recommendation}")
    print(f"signal_advisory_semantics_policy_source: {result.signal_advisory_semantics_policy_source}")
    print(f"signal_advisory_semantics_policy_version: {result.signal_advisory_semantics_policy_version}")
    print(f"signal_advisory_semantics_action: {result.signal_advisory_semantics_action}")
    print(f"signal_advisory_semantics_provenance_present: {result.signal_advisory_semantics_provenance_present}")
    print(
        "signal_advisory_semantics_missing_provenance_legacy_warning_only: "
        f"{result.signal_advisory_semantics_missing_provenance_legacy_warning_only}"
    )
    print(f"latest_single_symbol_advisory_run_id: {result.latest_single_symbol_advisory_run_id}")
    print(f"latest_single_symbol_advisory_symbol: {result.latest_single_symbol_advisory_symbol}")
    print(f"single_symbol_advisory_status: {result.single_symbol_advisory_status}")
    print(f"single_symbol_advisory_stage: {result.single_symbol_advisory_stage}")
    print(f"single_symbol_advisory_action: {result.single_symbol_advisory_action}")
    print(f"single_symbol_advisory_health_status: {result.single_symbol_advisory_health_status}")
    print(f"single_symbol_advisory_final_score: {result.single_symbol_advisory_final_score}")
    print(f"single_symbol_advisory_demo_mode: {result.single_symbol_advisory_demo_mode}")
    print(
        "single_symbol_advisory_not_strategy_recommendation: "
        f"{result.single_symbol_advisory_not_strategy_recommendation}"
    )
    print(f"single_symbol_advisory_alert_preview_path: {result.single_symbol_advisory_alert_preview_path}")
    print(f"single_symbol_advisory_next_action: {result.single_symbol_advisory_next_action}")
    print(
        "single_symbol_advisory_semantics_policy_source: "
        f"{result.single_symbol_advisory_semantics_policy_source}"
    )
    print(
        "single_symbol_advisory_semantics_policy_version: "
        f"{result.single_symbol_advisory_semantics_policy_version}"
    )
    print(f"single_symbol_advisory_semantics_action: {result.single_symbol_advisory_semantics_action}")
    print(
        "single_symbol_advisory_semantics_provenance_present: "
        f"{result.single_symbol_advisory_semantics_provenance_present}"
    )
    print(
        "single_symbol_advisory_semantics_missing_provenance_legacy_warning_only: "
        f"{result.single_symbol_advisory_semantics_missing_provenance_legacy_warning_only}"
    )
    print(f"latest_single_symbol_advisory_answer_run_id: {result.latest_single_symbol_advisory_answer_run_id}")
    print(f"latest_single_symbol_advisory_answer_symbol: {result.latest_single_symbol_advisory_answer_symbol}")
    print(f"single_symbol_advisory_answer_status: {result.single_symbol_advisory_answer_status}")
    print(f"single_symbol_advisory_answer_stage: {result.single_symbol_advisory_answer_stage}")
    print(f"single_symbol_advisory_answer_action: {result.single_symbol_advisory_answer_action}")
    print(f"single_symbol_advisory_answer_health_status: {result.single_symbol_advisory_answer_health_status}")
    print(f"single_symbol_advisory_answer_question: {result.single_symbol_advisory_answer_question}")
    print(f"single_symbol_advisory_answer_style: {result.single_symbol_advisory_answer_style}")
    print(f"single_symbol_advisory_answer_demo_mode: {result.single_symbol_advisory_answer_demo_mode}")
    print(
        "single_symbol_advisory_answer_not_strategy_recommendation: "
        f"{result.single_symbol_advisory_answer_not_strategy_recommendation}"
    )
    print(f"single_symbol_advisory_answer_markdown_path: {result.single_symbol_advisory_answer_markdown_path}")
    print(f"single_symbol_advisory_answer_next_action: {result.single_symbol_advisory_answer_next_action}")
    print(
        "single_symbol_advisory_answer_semantics_policy_source: "
        f"{result.single_symbol_advisory_answer_semantics_policy_source}"
    )
    print(
        "single_symbol_advisory_answer_semantics_policy_version: "
        f"{result.single_symbol_advisory_answer_semantics_policy_version}"
    )
    print(
        "single_symbol_advisory_answer_semantics_action: "
        f"{result.single_symbol_advisory_answer_semantics_action}"
    )
    print(
        "single_symbol_advisory_answer_semantics_provenance_present: "
        f"{result.single_symbol_advisory_answer_semantics_provenance_present}"
    )
    print(
        "single_symbol_advisory_answer_semantics_missing_provenance_legacy_warning_only: "
        f"{result.single_symbol_advisory_answer_semantics_missing_provenance_legacy_warning_only}"
    )
    print(f"latest_advisory_conversation_run_id: {result.latest_advisory_conversation_run_id}")
    print(f"advisory_conversation_original_question: {result.advisory_conversation_original_question}")
    print(f"advisory_conversation_parsed_symbol: {result.advisory_conversation_parsed_symbol}")
    print(f"advisory_conversation_parsed_intent: {result.advisory_conversation_parsed_intent}")
    print(f"advisory_conversation_status: {result.advisory_conversation_status}")
    print(f"advisory_conversation_stage: {result.advisory_conversation_stage}")
    print(f"advisory_conversation_action: {result.advisory_conversation_action}")
    print(f"advisory_conversation_health_status: {result.advisory_conversation_health_status}")
    print(f"advisory_conversation_parser_type: {result.advisory_conversation_parser_type}")
    print(f"advisory_conversation_llm_api_called: {result.advisory_conversation_llm_api_called}")
    print(f"advisory_conversation_no_message_sent: {result.advisory_conversation_no_message_sent}")
    print(f"advisory_conversation_no_live_trading: {result.advisory_conversation_no_live_trading}")
    print(f"advisory_conversation_no_broker_api: {result.advisory_conversation_no_broker_api}")
    print(f"advisory_conversation_auto_order_allowed: {result.advisory_conversation_auto_order_allowed}")
    print(f"advisory_conversation_linked_answer_path: {result.advisory_conversation_linked_answer_path}")
    print(f"advisory_conversation_next_action: {result.advisory_conversation_next_action}")
    print(f"advisory_conversation_semantics_policy_source: {result.advisory_conversation_semantics_policy_source}")
    print(f"advisory_conversation_semantics_policy_version: {result.advisory_conversation_semantics_policy_version}")
    print(f"advisory_conversation_semantics_action: {result.advisory_conversation_semantics_action}")
    print(
        "advisory_conversation_semantics_provenance_present: "
        f"{result.advisory_conversation_semantics_provenance_present}"
    )
    print(
        "advisory_conversation_semantics_missing_provenance_legacy_warning_only: "
        f"{result.advisory_conversation_semantics_missing_provenance_legacy_warning_only}"
    )
    print(f"latest_semantics_action: {result.latest_semantics_action}")
    print(f"semantics_provenance_present: {result.semantics_provenance_present}")
    print(f"semantics_provenance_missing_legacy_count: {result.semantics_provenance_missing_legacy_count}")
    print(f"latest_market_update_handoff_id: {result.latest_market_update_handoff_id}")
    print(f"market_update_handoff_status: {result.market_update_handoff_status}")
    print(f"market_update_handoff_stage: {result.market_update_handoff_stage}")
    print(f"market_update_handoff_current_candidate_run_id: {result.market_update_handoff_current_candidate_run_id}")
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
        source=args.source,
        upstream_source=args.upstream_source,
        cache_path=args.cache_path,
        output_path=args.output,
        config=settings,
    )
    print(f"Market cache query status: {result.status}")
    print(f"cache_path: {result.cache_path}")
    print(f"symbol: {result.symbol}")
    print(f"source_filter: {result.audit_metadata.get('source_filter', '')}")
    print(f"upstream_source_filter: {result.audit_metadata.get('upstream_source_filter', '')}")
    print(f"row_count: {result.row_count}")
    print(f"symbol_count: {result.audit_metadata.get('symbol_count', 0)}")
    if not result.result_frame.empty:
        print(f"date_range: {result.result_frame['trade_date'].min()} to {result.result_frame['trade_date'].max()}")
    else:
        print("date_range: ")
    print(f"source_counts: {json.dumps(result.audit_metadata.get('source_counts', {}), sort_keys=True)}")
    print(f"upstream_counts: {json.dumps(result.audit_metadata.get('upstream_counts', {}), sort_keys=True)}")
    if result.output_path is not None:
        print(f"output_path: {result.output_path}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0 if result.status != "FAIL" else 1


def _handle_market_cache_export(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {}
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    if args.export_output_dir:
        updates["export_output_dir"] = Path(args.export_output_dir)
    if args.manifest_output_dir:
        updates["manifest_output_dir"] = Path(args.manifest_output_dir)
    if args.fail_fast:
        updates["fail_fast"] = True
    if updates:
        settings = settings.model_copy(
            update={
                "market_cache_export": settings.market_cache_export.model_copy(update=updates)
            }
        )
    result = run_market_cache_export(
        args.manifest,
        cache_path=args.cache_path,
        output_dir=args.output_dir,
        export_output_dir=args.export_output_dir,
        manifest_output_dir=args.manifest_output_dir,
        build_pipeline_manifest=bool(args.build_pipeline_manifest),
        universe=args.universe,
        trading_calendar=args.trading_calendar,
        fail_fast=True if args.fail_fast else None,
        config=settings,
    )
    print(f"Market cache export status: {result.status}")
    print(f"export_id: {result.export_id}")
    print(f"manifest: {result.manifest_path}")
    print(f"exported_market_csv_path: {result.exported_market_csv_path}")
    print(f"row_count: {result.row_count}")
    print(f"duplicate_key_count: {result.duplicate_key_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"generated_pipeline_manifest_path: {result.pipeline_manifest_path or ''}")
    print(f"Report path: {result.artifact_paths['market_cache_export_report']}")
    print(f"Rows CSV path: {result.artifact_paths['market_cache_export_rows']}")
    print(f"Issues CSV path: {result.artifact_paths['market_cache_export_issues']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0 if result.status != "FAIL" else 1


def _handle_market_cache_export_plan(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {}
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    if args.manifest_output_dir:
        updates["manifest_output_dir"] = Path(args.manifest_output_dir)
    if args.strict_reliable:
        updates["strict_reliable"] = True
    if args.fail_fast:
        updates["fail_fast"] = True
    if updates:
        settings = settings.model_copy(
            update={
                "market_cache_export_policy": settings.market_cache_export_policy.model_copy(update=updates)
            }
        )
    result = run_market_cache_export_policy_plan(
        args.manifest,
        cache_path=args.cache_path,
        output_dir=args.output_dir,
        manifest_output_dir=args.manifest_output_dir,
        strict_reliable=True if args.strict_reliable else None,
        fail_fast=True if args.fail_fast else None,
        config=settings,
    )
    status_counts = {}
    if not result.recommendations_frame.empty:
        status_counts = {
            str(key): int(value)
            for key, value in result.recommendations_frame["status"].value_counts().sort_index().items()
        }
    print(f"Market cache export plan status: {result.status}")
    print(f"plan_id: {result.plan_id}")
    print(f"manifest: {result.manifest_path}")
    print(f"generated_reviewed_manifest_path: {result.recommended_manifest_path}")
    print(f"recommendation_count: {result.recommendation_count}")
    print(f"status_counts: {json.dumps(status_counts, sort_keys=True)}")
    print(f"issue_count: {result.issue_count}")
    print(f"Report path: {result.artifact_paths['market_cache_export_policy_report']}")
    print(f"Recommendations CSV path: {result.artifact_paths['market_cache_export_policy_recommendations']}")
    print(f"Issues CSV path: {result.artifact_paths['market_cache_export_policy_issues']}")
    for row in result.recommendations_frame.to_dict("records"):
        if row.get("status") in {"RECOMMENDED", "RECOMMENDED_WITH_WARNINGS"}:
            comparison = row.get("comparison_status", "")
            reference = ""
            if row.get("comparison_reference_source"):
                reference = f" vs {row.get('comparison_reference_source')}/{row.get('comparison_reference_upstream')}"
            print(
                "RECOMMENDATION: "
                f"{row.get('symbol')} -> {row.get('recommended_source')}/{row.get('recommended_upstream_source')} "
                f"({row.get('status')}); comparison={comparison}{reference}"
            )
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0 if result.status != "FAIL" else 1


def _handle_market_cache_export_plan_index(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"include_missing_metadata": bool(args.include_missing_metadata)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "market_cache_export_policy_index": settings.market_cache_export_policy_index.model_copy(update=updates)
        }
    )
    result = build_market_cache_export_policy_index(
        root=args.root,
        output_dir=args.output_dir,
        include_missing_metadata=bool(args.include_missing_metadata),
        settings=settings,
    )
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index report path: {result.artifact_paths['market_cache_export_policy_index_report']}")
    print(f"Index CSV path: {result.artifact_paths['market_cache_export_policy_index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    if not result.index_frame.empty:
        print(f"comparison_pass_count: {_sum_cli_column(result.index_frame, 'comparison_pass_count')}")
        print(f"comparison_warn_count: {_sum_cli_column(result.index_frame, 'comparison_warn_count')}")
        print(f"comparison_fail_count: {_sum_cli_column(result.index_frame, 'comparison_fail_count')}")
        print(f"comparison_unavailable_count: {_sum_cli_column(result.index_frame, 'comparison_unavailable_count')}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_market_cache_export_plan_health(args: argparse.Namespace) -> int:
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
            "market_cache_export_policy_health": settings.market_cache_export_policy_health.model_copy(update=updates)
        }
    )
    result = check_market_cache_export_policy_health(
        index_path=args.index,
        root=None if args.index else args.root,
        output_dir=args.output_dir,
        settings=settings,
    )
    print(f"Market cache export plan health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    health_summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"comparison_pass_count: {health_summary.get('comparison_pass_count', 0)}")
    print(f"comparison_warn_count: {health_summary.get('comparison_warn_count', 0)}")
    print(f"comparison_fail_count: {health_summary.get('comparison_fail_count', 0)}")
    print(f"comparison_unavailable_count: {health_summary.get('comparison_unavailable_count', 0)}")
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Report path: {result.artifact_paths['market_cache_export_policy_health_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict and not args.allow_warn:
        return 1
    return 0


def _handle_market_cache_export_plan_status(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "market_cache_export_policy_status": settings.market_cache_export_policy_status.model_copy(update=updates)
        }
    )
    result = run_market_cache_export_policy_status(
        root=args.root,
        output_dir=args.output_dir,
        config=settings,
    )
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Market cache export plan workflow status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_plan_id: {result.latest_plan_id}")
    print(f"recommendation_count: {summary.get('recommendation_count', 0)}")
    print(f"recommended_count: {summary.get('recommended_count', 0)}")
    print(f"recommended_with_warnings_count: {summary.get('recommended_with_warnings_count', 0)}")
    print(f"comparison_pass_count: {summary.get('comparison_pass_count', 0)}")
    print(f"comparison_warn_count: {summary.get('comparison_warn_count', 0)}")
    print(f"comparison_fail_count: {summary.get('comparison_fail_count', 0)}")
    print(f"comparison_unavailable_count: {summary.get('comparison_unavailable_count', 0)}")
    print(f"generated_reviewed_manifest_path: {summary.get('generated_reviewed_manifest_path', '')}")
    print(f"downstream_export_id: {summary.get('downstream_export_id', '')}")
    print(f"downstream_snapshot_quality_status: {summary.get('downstream_snapshot_quality_status', '')}")
    print(f"next_manual_action: {result.next_manual_action}")
    print(f"Report path: {result.artifact_paths['market_cache_export_policy_status_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict:
        return 1
    return 0


def _handle_market_cache_export_index(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"include_missing_metadata": bool(args.include_missing_metadata)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "market_cache_export_index": settings.market_cache_export_index.model_copy(update=updates)
        }
    )
    result = build_market_cache_export_index(
        root=args.root,
        output_dir=args.output_dir,
        include_missing_metadata=bool(args.include_missing_metadata),
        settings=settings,
    )
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Index report path: {result.artifact_paths['market_cache_export_index_report']}")
    print(f"Index CSV path: {result.artifact_paths['market_cache_export_index_csv']}")
    print(f"artifact_count: {result.artifact_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_market_cache_export_health(args: argparse.Namespace) -> int:
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
            "market_cache_export_health": settings.market_cache_export_health.model_copy(update=updates)
        }
    )
    result = check_market_cache_export_health(
        index_path=args.index,
        root=None if args.index else args.root,
        output_dir=args.output_dir,
        settings=settings,
    )
    print(f"Market cache export health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Report path: {result.artifact_paths['market_cache_export_health_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict and not args.allow_warn:
        return 1
    return 0


def _handle_market_cache_export_status(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {"strict": bool(args.strict)}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    settings = settings.model_copy(
        update={
            "market_cache_export_status": settings.market_cache_export_status.model_copy(update=updates)
        }
    )
    result = run_market_cache_export_status(
        root=args.root,
        output_dir=args.output_dir,
        config=settings,
    )
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Market cache export workflow status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_export_id: {result.latest_export_id}")
    print(f"exported_row_count: {summary.get('exported_row_count', 0)}")
    print(f"duplicate_key_count: {summary.get('duplicate_key_count', 0)}")
    print(f"pipeline_id: {summary.get('pipeline_id', '')}")
    print(f"data_pipeline_status: {summary.get('data_pipeline_status', '')}")
    print(f"data_quality_status: {summary.get('data_quality_status', '')}")
    print(f"snapshot_quality_status: {summary.get('snapshot_quality_status', '')}")
    print(f"next_manual_action: {result.next_manual_action}")
    print(f"Report path: {result.artifact_paths['market_cache_export_status_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict:
        return 1
    return 0


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


def _handle_market_cache_preflight(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {}
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    if args.strict_provisional:
        updates["strict_provisional"] = True
    if updates:
        settings = settings.model_copy(
            update={
                "market_cache_preflight": settings.market_cache_preflight.model_copy(update=updates)
            }
        )
    result = run_market_cache_preflight(
        args.input,
        metadata_path=args.metadata,
        health_metadata_path=args.health_metadata,
        reference_source=args.reference_source,
        cache_path=args.cache_path,
        required_fields=args.require_fields,
        symbol=args.symbol,
        start_date=args.start_date,
        end_date=args.end_date,
        output_dir=args.output_dir,
        strict_provisional=True if args.strict_provisional else None,
        config=settings,
    )
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Market cache preflight status: {result.status}")
    print(f"preflight_id: {result.preflight_id}")
    print(f"input_path: {result.input_path}")
    print(f"source: {summary.get('source', '')}")
    print(f"upstream_source: {summary.get('upstream_source', '')}")
    print(f"symbol: {summary.get('symbol', '')}")
    print(f"row_count: {summary.get('row_count', 0)}")
    print(f"required_fields: {summary.get('required_fields', '')}")
    print(f"reference_source: {summary.get('reference_source', '')}")
    print(f"comparison_status: {summary.get('comparison_status', '')}")
    print(f"issue_count: {summary.get('issue_count', 0)}")
    print(f"warning_count: {summary.get('warning_count', 0)}")
    print(f"error_count: {summary.get('error_count', 0)}")
    print(f"Report path: {result.artifact_paths['market_cache_preflight_report']}")
    print(f"Issues CSV path: {result.artifact_paths['market_cache_preflight_issues']}")
    print(f"Summary CSV path: {result.artifact_paths['market_cache_preflight_summary']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0 if result.status != "REJECT" else 1


def _handle_market_daily_update(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    if args.output_dir:
        settings = settings.model_copy(
            update={
                "market_daily_update": settings.market_daily_update.model_copy(
                    update={"output_dir": Path(args.output_dir)}
                )
            }
        )
    if args.symbol_manifest:
        result = run_market_daily_update_manifest(
            args.symbol_manifest,
            allow_real_data=bool(args.allow_real_data),
            dry_run=True if args.dry_run else None,
            accept_cache_write=bool(args.accept_cache_write),
            fail_fast=True if args.fail_fast else None,
            cache_path=args.cache_path,
            output_dir=args.output_dir,
            raw_output_dir=args.raw_output_dir,
            config=settings,
        )
        counts = result.audit_metadata.get("symbol_result_counts", {})
        print(f"Market daily update status: {result.status}")
        print(f"update_id: {result.update_id}")
        print(f"symbol_manifest: {result.manifest_path}")
        print(f"symbol_row_count: {len(result.symbol_results_frame)}")
        print(f"pass_count: {counts.get('PASS', 0)}")
        print(f"warn_count: {counts.get('WARN', 0)}")
        print(f"fail_count: {counts.get('FAIL', 0)}")
        print(f"skipped_disabled_count: {counts.get('SKIPPED_DISABLED', 0)}")
        print(f"blocked_needs_allow_real_data_count: {counts.get('BLOCKED_NEEDS_ALLOW_REAL_DATA', 0)}")
        print(f"blocked_missing_raw_input_count: {counts.get('BLOCKED_MISSING_RAW_INPUT', 0)}")
        print(f"blocked_missing_metadata_count: {counts.get('BLOCKED_MISSING_METADATA', 0)}")
        print(f"blocked_preflight_reject_count: {counts.get('BLOCKED_PREFLIGHT_REJECT', 0)}")
        print(f"cache_write_occurred: {result.cache_write_occurred}")
        print(f"Report path: {result.artifact_paths['market_daily_update_report']}")
        print(f"Steps CSV path: {result.artifact_paths['market_daily_update_steps']}")
        print(f"Symbol results CSV path: {result.artifact_paths['market_daily_update_symbol_results']}")
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        print("No live trading or broker API was invoked.")
        return 0 if result.status != "FAIL" else 1
    result = run_market_daily_update(
        source=args.source,
        symbol=args.symbol,
        start_date=args.start_date,
        end_date=args.end_date,
        raw_input=args.raw_input,
        metadata_path=args.metadata,
        allow_real_data=bool(args.allow_real_data),
        dry_run=True if args.dry_run else None,
        accept_cache_write=bool(args.accept_cache_write),
        reference_source=args.reference_source,
        required_fields=args.require_fields,
        cache_path=args.cache_path,
        raw_output_dir=args.raw_output_dir,
        revision_id=args.revision_id,
        preferred_upstream=args.preferred_upstream,
        strict_provisional=True if args.strict_provisional else None,
        output_dir=args.output_dir,
        config=settings,
    )
    print(f"Market daily update status: {result.status}")
    print(f"update_id: {result.update_id}")
    print(f"source: {result.request.source}")
    print(f"symbol: {result.request.symbol}")
    print(f"date_range: {result.request.start_date} to {result.request.end_date}")
    print(f"raw_data_path: {result.raw_data_path or ''}")
    print(f"metadata_path: {result.metadata_path or ''}")
    print(f"preflight_status: {result.preflight_result.status if result.preflight_result is not None else ''}")
    print(f"cache_write_occurred: {result.cache_write_occurred}")
    print(f"Report path: {result.artifact_paths['market_daily_update_report']}")
    print(f"Steps CSV path: {result.artifact_paths['market_daily_update_steps']}")
    print(f"Symbol results CSV path: {result.artifact_paths['market_daily_update_symbol_results']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0 if result.status != "FAIL" else 1


def _handle_historical_backfill(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    if args.output_dir:
        settings = settings.model_copy(
            update={
                "historical_backfill": settings.historical_backfill.model_copy(
                    update={"output_dir": Path(args.output_dir)}
                )
            }
        )
    result = run_historical_backfill(
        args.manifest,
        allow_real_data=bool(args.allow_real_data),
        dry_run=True if args.dry_run else None,
        accept_cache_write=bool(args.accept_cache_write),
        fail_fast=True if args.fail_fast else None,
        cache_path=args.cache_path,
        raw_output_dir=args.raw_output_dir,
        output_dir=args.output_dir,
        config=settings,
    )
    counts = result.audit_metadata.get("task_result_counts", {})
    fail_count = sum(
        int(counts.get(status, 0))
        for status in [
            "FAIL",
            "BLOCKED_NEEDS_ALLOW_REAL_DATA",
            "BLOCKED_PREFLIGHT_REJECT",
            "BLOCKED_MISSING_RAW_INPUT",
        ]
    )
    print(f"Historical backfill status: {result.status}")
    print(f"backfill_id: {result.backfill_id}")
    print(f"manifest: {result.manifest_path}")
    print(f"task_count: {result.task_count}")
    print(f"pass_count: {counts.get('PASS', 0)}")
    print(f"warn_count: {counts.get('WARN', 0)}")
    print(f"fail_count: {fail_count}")
    print(f"skipped_disabled_count: {counts.get('SKIPPED_DISABLED', 0)}")
    print(f"blocked_needs_allow_real_data_count: {counts.get('BLOCKED_NEEDS_ALLOW_REAL_DATA', 0)}")
    print(f"blocked_missing_raw_input_count: {counts.get('BLOCKED_MISSING_RAW_INPUT', 0)}")
    print(f"blocked_preflight_reject_count: {counts.get('BLOCKED_PREFLIGHT_REJECT', 0)}")
    print(f"cache_write_occurred: {result.cache_write_occurred}")
    print(f"Report path: {result.artifact_paths['historical_backfill_report']}")
    print(f"Tasks CSV path: {result.artifact_paths['historical_backfill_tasks']}")
    print(f"Results CSV path: {result.artifact_paths['historical_backfill_results']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0 if result.status != "FAIL" else 1


def _handle_historical_backfill_index(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    if args.include_missing_metadata:
        updates["include_missing_metadata"] = True
    if updates:
        settings = settings.model_copy(
            update={
                "historical_backfill_index": settings.historical_backfill_index.model_copy(update=updates)
            }
        )
    result = build_historical_backfill_index(settings=settings)
    print(f"artifact_count: {result.artifact_count}")
    print(f"Index report path: {result.artifact_paths['historical_backfill_index_report']}")
    print(f"Index CSV path: {result.artifact_paths['historical_backfill_index_csv']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_historical_backfill_health(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    if args.index:
        updates["index_path"] = Path(args.index)
    if args.strict:
        updates["strict"] = True
    if updates:
        settings = settings.model_copy(
            update={
                "historical_backfill_health": settings.historical_backfill_health.model_copy(update=updates)
            }
        )
    result = check_historical_backfill_health(
        index_path=args.index,
        root=None if args.index else args.root,
        settings=settings,
    )
    print(f"Health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(f"Report path: {result.artifact_paths['historical_backfill_health_report']}")
    print(f"Issues CSV path: {result.artifact_paths['historical_backfill_health_issues']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict and not args.allow_warn:
        return 1
    return 0


def _handle_historical_backfill_status(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    if args.strict:
        updates["strict"] = True
    if updates:
        settings = settings.model_copy(
            update={
                "historical_backfill_status": settings.historical_backfill_status.model_copy(update=updates)
            }
        )
    result = run_historical_backfill_status(
        root=args.root,
        output_dir=args.output_dir,
        config=settings,
    )
    print(f"Historical backfill workflow status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_backfill_id: {result.latest_backfill_id}")
    print(f"next_manual_action: {result.next_manual_action}")
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"accepted_task_count: {summary.get('accepted_task_count', 0)}")
    print(f"rejected_task_count: {summary.get('rejected_task_count', 0)}")
    print(f"preflight_rejected_count: {summary.get('preflight_rejected_count', 0)}")
    print(f"comparison_failed_count: {summary.get('comparison_failed_count', 0)}")
    print(f"cache_write_partial: {summary.get('cache_write_partial', False)}")
    print(f"rejected_symbols: {summary.get('rejected_symbols', '')}")
    print(f"rejected_issue_categories: {summary.get('rejected_issue_categories', '')}")
    print(f"Report path: {result.artifact_paths['historical_backfill_status_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict:
        return 1
    return 0


def _handle_market_update_handoff(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    if args.output_dir:
        settings = settings.model_copy(
            update={
                "market_update_handoff": settings.market_update_handoff.model_copy(
                    update={"output_dir": Path(args.output_dir)}
                )
            }
        )
    run_validation = False if args.skip_validation else (True if args.run_pipeline else None)
    result = run_market_update_snapshot_handoff(
        symbol_manifest=args.symbol_manifest,
        market_daily_update_dir=args.market_daily_update_dir,
        universe=args.universe,
        trading_calendar=args.trading_calendar,
        decision_date=args.decision_date,
        universe_name=args.universe_name,
        selection_profile=args.selection_profile,
        top_n=args.top,
        strict_accept_only=bool(args.strict_accept_only),
        dry_run=bool(args.dry_run),
        run_validation=run_validation,
        output_dir=args.output_dir,
        config=settings,
    )
    current = result.current_candidate_result
    pipeline = result.pipeline_result
    snapshot = result.snapshot_quality_result
    print(f"Market update handoff status: {result.status}")
    print(f"handoff_id: {result.handoff_id}")
    print(f"included_row_count: {result.included_row_count}")
    print(f"batch_market_csv_path: {result.batch_market_csv_path or ''}")
    print(f"generated_pipeline_manifest_path: {result.pipeline_manifest_path or ''}")
    print(f"pipeline_id: {pipeline.pipeline_id if pipeline is not None else ''}")
    print(f"pipeline_status: {pipeline.status if pipeline is not None else ''}")
    print(f"snapshot_quality_status: {snapshot.status if snapshot is not None else ''}")
    print(f"current_candidate_run_id: {current.run_id if current is not None else ''}")
    print(f"factor_dataset_shape: {tuple(current.factor_dataset.shape) if current is not None else (0, 0)}")
    print(f"scored_dataset_shape: {tuple(current.scored_dataset.shape) if current is not None else (0, 0)}")
    print(f"candidates_shape: {tuple(current.candidates.shape) if current is not None else (0, 0)}")
    print(f"candidate_count: {current.candidate_count if current is not None else 0}")
    print(f"Report path: {result.artifact_paths['market_update_handoff_report']}")
    print(f"Rows CSV path: {result.artifact_paths['market_update_handoff_rows']}")
    print(f"Generated manifest artifact path: {result.artifact_paths['generated_pipeline_manifest']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0 if result.status != "FAIL" else 1


def _handle_market_update_handoff_index(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    if args.include_missing_metadata:
        updates["include_missing_metadata"] = True
    if updates:
        settings = settings.model_copy(
            update={
                "market_update_handoff_index": settings.market_update_handoff_index.model_copy(update=updates)
            }
        )
    result = build_market_update_handoff_index(settings=settings)
    print(f"artifact_count: {result.artifact_count}")
    print(f"Index report path: {result.artifact_paths['market_update_handoff_index']}")
    print(f"Index CSV path: {result.artifact_paths['market_update_handoff_index_csv']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_market_update_handoff_health(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    if args.strict:
        updates["strict"] = True
    if updates:
        settings = settings.model_copy(
            update={
                "market_update_handoff_health": settings.market_update_handoff_health.model_copy(update=updates)
            }
        )
    result = check_market_update_handoff_health(
        index_path=args.index,
        root=args.root,
        settings=settings,
    )
    print(f"Market update handoff health status: {result.status}")
    print(f"checked_artifact_count: {result.checked_artifact_count}")
    print(f"issue_count: {result.issue_count}")
    print(f"warning_count: {result.warning_count}")
    print(f"error_count: {result.error_count}")
    print(f"Report path: {result.artifact_paths['market_update_handoff_health_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict and not args.allow_warn:
        return 1
    return 0


def _handle_market_update_handoff_status(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    updates = {}
    if args.root:
        updates["root_dir"] = Path(args.root)
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir)
    if args.strict:
        updates["strict"] = True
    if updates:
        settings = settings.model_copy(
            update={
                "market_update_handoff_status": settings.market_update_handoff_status.model_copy(update=updates)
            }
        )
    result = run_market_update_handoff_status(
        root=args.root,
        output_dir=args.output_dir,
        config=settings,
    )
    print(f"Market update handoff status: {result.status}")
    print(f"workflow_stage: {result.workflow_stage}")
    print(f"latest_handoff_id: {result.latest_handoff_id}")
    print(f"next_manual_action: {result.next_manual_action}")
    print(f"Report path: {result.artifact_paths['market_update_handoff_status_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL":
        return 1
    if result.status == "WARN" and args.strict:
        return 1
    return 0


def _handle_market_cache_compare(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    if args.output_dir:
        settings = settings.model_copy(
            update={
                "market_data_comparison": settings.market_data_comparison.model_copy(
                    update={"output_dir": Path(args.output_dir)}
                )
            }
        )
    result = run_market_source_comparison(
        symbol=args.symbol,
        source_a=args.source_a,
        source_b=args.source_b,
        start_date=args.start_date,
        end_date=args.end_date,
        cache_path=args.cache_path,
        output_dir=args.output_dir,
        config=settings,
    )
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    print(f"Market cache comparison status: {result.status}")
    print(f"comparison_id: {result.comparison_id}")
    print(f"cache_path: {result.cache_path}")
    print(f"symbol: {result.symbol}")
    print(f"source_a: {result.source_a}")
    print(f"source_b: {result.source_b}")
    print(f"matched_row_count: {summary.get('matched_row_count', 0)}")
    print(f"source_a_only_count: {summary.get('source_a_only_count', 0)}")
    print(f"source_b_only_count: {summary.get('source_b_only_count', 0)}")
    print(f"max_close_diff_pct: {summary.get('max_close_diff_pct', 0)}")
    print(f"max_volume_diff_pct: {summary.get('max_volume_diff_pct', 0)}")
    print(f"max_amount_diff_pct: {summary.get('max_amount_diff_pct', 0)}")
    print(f"median_volume_ratio: {summary.get('median_volume_ratio', '')}")
    print(f"median_amount_ratio: {summary.get('median_amount_ratio', '')}")
    print(f"suspected_volume_scale_factor: {summary.get('suspected_volume_scale_factor', '')}")
    print(f"suspected_amount_scale_factor: {summary.get('suspected_amount_scale_factor', '')}")
    print(f"diagnostic_classification: {summary.get('diagnostic_classification', 'NO_UNIT_MISMATCH')}")
    print(f"recommended_for_price: {summary.get('recommended_for_price', '')}")
    print(f"recommended_for_volume: {summary.get('recommended_for_volume', '')}")
    print(f"recommended_for_amount: {summary.get('recommended_for_amount', '')}")
    print(f"amount_sensitive_preferred_source: {summary.get('amount_sensitive_preferred_source', '')}")
    print(f"pre_close_caveat: {summary.get('pre_close_caveat', '')}")
    print(f"pass_count: {summary.get('pass_count', 0)}")
    print(f"warn_count: {summary.get('warn_count', 0)}")
    print(f"fail_count: {summary.get('fail_count', 0)}")
    print(f"Report path: {result.artifact_paths['market_data_comparison_report']}")
    print(f"Rows CSV path: {result.artifact_paths['market_data_comparison_rows']}")
    print(f"Summary CSV path: {result.artifact_paths['market_data_comparison_summary']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0 if result.status != "FAIL" else 1


def _handle_market_source_policy(args: argparse.Namespace) -> int:
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    if args.output_dir:
        settings = settings.model_copy(
            update={
                "market_source_policy": settings.market_source_policy.model_copy(
                    update={"output_dir": Path(args.output_dir)}
                )
            }
        )
    result = run_market_source_policy_report(
        output_dir=args.output_dir,
        config=settings,
    )
    print(f"Market source policy status: {result.status}")
    print(f"policy_report_id: {result.policy_report_id}")
    print(f"row_count: {result.row_count}")
    print(f"Report path: {result.artifact_paths['market_source_policy_report']}")
    print(f"Policy CSV path: {result.artifact_paths['market_source_policy_csv']}")
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


def _parse_int_values(value: str | Sequence[str] | None) -> list[int]:
    if value is None:
        return []
    raw_values = value if isinstance(value, (list, tuple)) else [value]
    output: list[int] = []
    for raw_value in raw_values:
        parts = [part.strip() for part in str(raw_value).split(",")]
        output.extend(int(part) for part in parts if part)
    return output


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


def _sum_cli_column(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(pd.to_numeric(frame[column], errors="coerce").fillna(0).sum())


if __name__ == "__main__":
    raise SystemExit(main())
