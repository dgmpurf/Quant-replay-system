from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.metric_extension import (
    ALLOWED_EXTENSION_METRIC_SET,
    EXACT_METRIC_EXTENSION_APPROVAL_TEXT,
    METRIC_EXTENSION_APPROVAL_BLOCKED,
    METRIC_EXTENSION_BENCHMARK_MAPPING_BLOCKED,
    METRIC_EXTENSION_DENOMINATOR_BLOCKED,
    METRIC_EXTENSION_HEALTH_BLOCKED,
    METRIC_EXTENSION_INDUSTRY_MAPPING_BLOCKED,
    METRIC_EXTENSION_LEAKAGE_BLOCKED,
    METRIC_EXTENSION_LINEAGE_BLOCKED,
    METRIC_EXTENSION_METRIC_COMPUTATION_INPUT_BLOCKED,
    METRIC_EXTENSION_METRIC_EVALUATION_INPUT_BLOCKED,
    METRIC_EXTENSION_OVERCLAIM_BLOCKED,
    METRIC_EXTENSION_REPORT_CREATED,
    METRIC_EXTENSION_RETURN_FIELD_BLOCKED,
    METRIC_EXTENSION_SAMPLE_SCOPE_BLOCKED,
    METRIC_EXTENSION_SIDE_EFFECT_BLOCKED,
    METRIC_EXTENSION_UNSUPPORTED_METRIC_BLOCKED,
    METRIC_EXTENSION_FORWARD_LABEL_INPUT_BLOCKED,
    METRIC_EXTENSION_REPLAY_FREEZE_INPUT_BLOCKED,
    METRIC_EXTENSION_TRAINING_EVALUATION_INPUT_BLOCKED,
    NO_METRIC_EXTENSION_INPUT,
    READY_FOR_METRIC_EXTENSION,
    MetricExtensionSettings,
    run_metric_extension,
)
from quant_replay_system.metric_extension_health import check_metric_extension_health
from quant_replay_system.metric_extension_index import build_metric_extension_index
from quant_replay_system.metric_extension_status import run_metric_extension_status
from quant_replay_system.local_research_dashboard import run_local_research_dashboard


DOWNSTREAM_FALSE_FIELDS = [
    "evaluation_execution_completed",
    "training_allowed",
    "weights_trained",
    "training_result_created",
    "model_version_created",
    "thresholds_optimized",
    "predictions_created",
    "calibrated_probabilities_created",
    "feature_importance_created",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "stock_profile_created",
    "buy_review_allowed",
    "real_buy_review_eligible",
    "approved_for_paper",
    "strategy_performance_validated",
    "trading_allowed",
    "order_placed",
    "broker_api_called",
    "message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
]


def test_no_input_writes_required_artifacts_with_safe_defaults(tmp_path: Path) -> None:
    result = run_metric_extension(MetricExtensionSettings(output_dir=_output_dir(tmp_path)))

    assert result.status == NO_METRIC_EXTENSION_INPUT
    assert result.workflow_stage == "METRIC_EXTENSION_NO_INPUT"
    assert result.ready_for_metric_extension is False
    assert result.metric_extension_executed is False
    assert result.metric_extension_report_created is False
    assert result.extended_metric_result_rows_created is False
    assert result.extended_metric_summary_created is False
    assert result.extended_metrics_computed is False
    assert result.allowed_extension_metric_set == ",".join(ALLOWED_EXTENSION_METRIC_SET)
    assert result.unsupported_metrics_requested is False
    assert result.sample_row_count == 0
    assert result.eligible_sample_count == 0
    assert result.quarantined_sample_count == 0
    assert result.benchmark_denominator_count == 0
    assert result.industry_denominator_count == 0
    _assert_downstream_flags_false(result)
    for key in _required_artifact_keys():
        assert result.artifact_paths[key].exists(), key
    metadata = _read_json(result.artifact_paths["metadata"])
    safety = _read_json(result.artifact_paths["safety_flags"])
    assert metadata["execution_status"] == NO_METRIC_EXTENSION_INPUT
    assert metadata["ready_for_metric_extension"] is False
    assert safety["extended_metrics_computed"] is False
    assert pd.read_csv(result.artifact_paths["result_rows"]).empty
    assert pd.read_csv(result.artifact_paths["summary"]).empty


@pytest.mark.parametrize("approval_text", ["", "continue", "go ahead", "extend metrics", "run evaluation", "train it"])
def test_missing_or_vague_approval_blocks(tmp_path: Path, approval_text: str) -> None:
    settings = _happy_settings(tmp_path)
    _write_json(settings.approval_manifest_path, {"approval_text": approval_text})

    result = run_metric_extension(settings)

    assert result.status == METRIC_EXTENSION_APPROVAL_BLOCKED
    assert result.ready_for_metric_extension is False
    assert result.extended_metrics_computed is False
    _assert_downstream_flags_false(result)


@pytest.mark.parametrize(
    "requested_metric",
    [
        "max_drawdown",
        "max_runup",
        "information_coefficient",
        "rank_information_coefficient",
        "sharpe_like_metric",
        "confidence_interval",
        "out_of_sample_metric",
        "regime_robustness",
        "false_positive_cost",
        "false_negative_opportunity_cost",
        "turnover",
        "slippage_sensitivity",
        "some_new_metric",
    ],
)
def test_unsupported_metric_requests_block(tmp_path: Path, requested_metric: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.metric_extension_request_manifest_path, {"requested_extension_metric_set": [requested_metric]})

    result = run_metric_extension(settings)

    assert result.status == METRIC_EXTENSION_UNSUPPORTED_METRIC_BLOCKED
    assert result.unsupported_metrics_requested is True
    assert result.extended_metric_result_rows_created is False


@pytest.mark.parametrize(
    ("request_patch", "expected_status"),
    [
        ({"training_result_requested": True}, METRIC_EXTENSION_OVERCLAIM_BLOCKED),
        ({"weights_requested": True}, METRIC_EXTENSION_OVERCLAIM_BLOCKED),
        ({"model_version_requested": True}, METRIC_EXTENSION_OVERCLAIM_BLOCKED),
        ({"thresholds_requested": True}, METRIC_EXTENSION_OVERCLAIM_BLOCKED),
        ({"predictions_requested": True}, METRIC_EXTENSION_OVERCLAIM_BLOCKED),
        ({"calibrated_probabilities_requested": True}, METRIC_EXTENSION_OVERCLAIM_BLOCKED),
        ({"feature_importance_requested": True}, METRIC_EXTENSION_OVERCLAIM_BLOCKED),
        ({"stock_profile_requested": True}, METRIC_EXTENSION_OVERCLAIM_BLOCKED),
        ({"buy_review_requested": True}, METRIC_EXTENSION_OVERCLAIM_BLOCKED),
        ({"paper_approval_requested": True}, METRIC_EXTENSION_OVERCLAIM_BLOCKED),
        ({"performance_validation_requested": True}, METRIC_EXTENSION_OVERCLAIM_BLOCKED),
        ({"trading_requested": True}, METRIC_EXTENSION_SIDE_EFFECT_BLOCKED),
    ],
)
def test_downstream_scope_requests_block(tmp_path: Path, request_patch: dict[str, object], expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.metric_extension_request_manifest_path, request_patch)

    result = run_metric_extension(settings)

    assert result.status == expected_status
    assert result.metric_extension_report_created is False
    _assert_downstream_flags_false(result)


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("metric_computation_metadata_path", METRIC_EXTENSION_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_result_rows_path", METRIC_EXTENSION_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_summary_path", METRIC_EXTENSION_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_status_artifact_path", METRIC_EXTENSION_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_health_artifact_path", METRIC_EXTENSION_HEALTH_BLOCKED),
        ("metric_evaluation_metadata_path", METRIC_EXTENSION_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_sample_scope_path", METRIC_EXTENSION_SAMPLE_SCOPE_BLOCKED),
        ("metric_evaluation_denominator_rules_path", METRIC_EXTENSION_DENOMINATOR_BLOCKED),
        ("metric_evaluation_status_artifact_path", METRIC_EXTENSION_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_health_artifact_path", METRIC_EXTENSION_HEALTH_BLOCKED),
        ("training_evaluation_metadata_path", METRIC_EXTENSION_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_sample_rows_path", METRIC_EXTENSION_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_status_artifact_path", METRIC_EXTENSION_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_health_artifact_path", METRIC_EXTENSION_HEALTH_BLOCKED),
        ("forward_return_label_metadata_path", METRIC_EXTENSION_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_rows_path", METRIC_EXTENSION_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_status_artifact_path", METRIC_EXTENSION_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_health_artifact_path", METRIC_EXTENSION_HEALTH_BLOCKED),
        ("replay_decision_freeze_metadata_path", METRIC_EXTENSION_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_rows_path", METRIC_EXTENSION_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_status_artifact_path", METRIC_EXTENSION_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_health_artifact_path", METRIC_EXTENSION_HEALTH_BLOCKED),
        ("benchmark_mapping_path", METRIC_EXTENSION_BENCHMARK_MAPPING_BLOCKED),
        ("industry_mapping_path", METRIC_EXTENSION_INDUSTRY_MAPPING_BLOCKED),
        ("benchmark_return_rows_path", METRIC_EXTENSION_BENCHMARK_MAPPING_BLOCKED),
        ("industry_return_rows_path", METRIC_EXTENSION_INDUSTRY_MAPPING_BLOCKED),
        ("leakage_evidence_bundle_path", METRIC_EXTENSION_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", METRIC_EXTENSION_OVERCLAIM_BLOCKED),
        ("side_effect_evidence_bundle_path", METRIC_EXTENSION_SIDE_EFFECT_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(tmp_path: Path, setting_name: str, expected_status: str) -> None:
    result = run_metric_extension(replace(_happy_settings(tmp_path), **{setting_name: None}))

    assert result.status == expected_status
    assert result.extended_metrics_computed is False


@pytest.mark.parametrize(
    ("path_name", "patch", "expected_status"),
    [
        ("metric_computation_metadata_path", {"status": "NO_METRIC_COMPUTATION_INPUT"}, METRIC_EXTENSION_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_health_artifact_path", {"status": "FAIL"}, METRIC_EXTENSION_HEALTH_BLOCKED),
        ("metric_evaluation_metadata_path", {"status": "NO_METRIC_EVALUATION_INPUT"}, METRIC_EXTENSION_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_health_artifact_path", {"status": "FAIL"}, METRIC_EXTENSION_HEALTH_BLOCKED),
        ("training_evaluation_metadata_path", {"status": "NO_TRAINING_EVALUATION_INPUT"}, METRIC_EXTENSION_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_health_artifact_path", {"status": "FAIL"}, METRIC_EXTENSION_HEALTH_BLOCKED),
        ("forward_return_label_metadata_path", {"status": "NO_FORWARD_RETURN_LABEL_INPUT"}, METRIC_EXTENSION_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_health_artifact_path", {"status": "FAIL"}, METRIC_EXTENSION_HEALTH_BLOCKED),
        ("replay_decision_freeze_metadata_path", {"status": "NO_REPLAY_DECISION_FREEZE_INPUT"}, METRIC_EXTENSION_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_health_artifact_path", {"status": "FAIL"}, METRIC_EXTENSION_HEALTH_BLOCKED),
        ("leakage_evidence_bundle_path", {"future_label_leakage": True}, METRIC_EXTENSION_LEAKAGE_BLOCKED),
        ("side_effect_evidence_bundle_path", {"broker_api_called": True}, METRIC_EXTENSION_SIDE_EFFECT_BLOCKED),
        ("overclaim_evidence_bundle_path", {"metric_extension_not_performance_validation": False}, METRIC_EXTENSION_OVERCLAIM_BLOCKED),
    ],
)
def test_gate_failures_block(tmp_path: Path, path_name: str, patch: dict[str, object], expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(getattr(settings, path_name), patch)

    result = run_metric_extension(settings)

    assert result.status == expected_status
    assert result.extended_metric_result_rows_created is False
    _assert_downstream_flags_false(result)


@pytest.mark.parametrize(
    ("path_name", "column", "expected_status"),
    [
        ("training_evaluation_sample_rows_path", "label_value", METRIC_EXTENSION_SAMPLE_SCOPE_BLOCKED),
        ("training_evaluation_sample_rows_path", "source_hash_coverage", METRIC_EXTENSION_LINEAGE_BLOCKED),
        ("training_evaluation_sample_rows_path", "revision_id_coverage", METRIC_EXTENSION_LINEAGE_BLOCKED),
        ("training_evaluation_sample_rows_path", "available_time_coverage", METRIC_EXTENSION_LINEAGE_BLOCKED),
        ("training_evaluation_sample_rows_path", "quality_status_coverage", METRIC_EXTENSION_LINEAGE_BLOCKED),
        ("benchmark_mapping_path", "benchmark_return_value", METRIC_EXTENSION_RETURN_FIELD_BLOCKED),
        ("benchmark_mapping_path", "benchmark_available_time", METRIC_EXTENSION_LINEAGE_BLOCKED),
        ("benchmark_mapping_path", "benchmark_source_hash", METRIC_EXTENSION_LINEAGE_BLOCKED),
        ("benchmark_mapping_path", "benchmark_revision_id", METRIC_EXTENSION_LINEAGE_BLOCKED),
        ("benchmark_mapping_path", "benchmark_quality_status", METRIC_EXTENSION_LINEAGE_BLOCKED),
        ("industry_mapping_path", "industry_return_value", METRIC_EXTENSION_RETURN_FIELD_BLOCKED),
        ("industry_mapping_path", "industry_classification_available_time", METRIC_EXTENSION_LINEAGE_BLOCKED),
        ("industry_mapping_path", "industry_source_hash", METRIC_EXTENSION_LINEAGE_BLOCKED),
        ("industry_mapping_path", "industry_revision_id", METRIC_EXTENSION_LINEAGE_BLOCKED),
        ("industry_mapping_path", "industry_quality_status", METRIC_EXTENSION_LINEAGE_BLOCKED),
    ],
)
def test_missing_required_columns_block(tmp_path: Path, path_name: str, column: str, expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    path = getattr(settings, path_name)
    rows = pd.read_csv(path, dtype={"symbol": "string"})
    rows.drop(columns=[column]).to_csv(path, index=False)

    result = run_metric_extension(settings)

    assert result.status == expected_status
    assert result.extended_metrics_computed is False


def test_duplicate_sample_rows_without_quarantine_blocks(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    rows = pd.read_csv(settings.training_evaluation_sample_rows_path, dtype={"symbol": "string"})
    rows = pd.concat([rows, rows.iloc[[0]]], ignore_index=True)
    rows.to_csv(settings.training_evaluation_sample_rows_path, index=False)

    result = run_metric_extension(settings)

    assert result.status == METRIC_EXTENSION_SAMPLE_SCOPE_BLOCKED


@pytest.mark.parametrize(
    ("column", "expected_benchmark", "expected_industry", "expected_quarantine"),
    [
        ("label_value", 2, 2, 1),
        ("benchmark_return_value", 2, 3, 1),
        ("industry_return_value", 3, 2, 1),
    ],
)
def test_non_numeric_values_are_quarantined_by_metric_denominator(
    tmp_path: Path,
    column: str,
    expected_benchmark: int,
    expected_industry: int,
    expected_quarantine: int,
) -> None:
    settings = _happy_settings(tmp_path)
    target_path = settings.training_evaluation_sample_rows_path
    if column.startswith("benchmark"):
        target_path = settings.benchmark_mapping_path
    if column.startswith("industry"):
        target_path = settings.industry_mapping_path
    rows = pd.read_csv(target_path, dtype={"symbol": "string"})
    rows[column] = rows[column].astype("object")
    rows.loc[0, column] = "bad"
    rows.to_csv(target_path, index=False)

    result = run_metric_extension(replace(settings, allow_metric_extension=True))

    assert result.status == METRIC_EXTENSION_REPORT_CREATED
    assert result.quarantined_sample_count == expected_quarantine
    assert result.benchmark_denominator_count == expected_benchmark
    assert result.industry_denominator_count == expected_industry


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_metric_extension(replace(_happy_settings(tmp_path), output_dir=tmp_path / "bad_outputs"))


def test_happy_path_without_allow_reaches_ready_and_creates_no_result_rows(tmp_path: Path) -> None:
    result = run_metric_extension(_happy_settings(tmp_path))

    assert result.status == READY_FOR_METRIC_EXTENSION
    assert result.workflow_stage == READY_FOR_METRIC_EXTENSION
    assert result.ready_for_metric_extension is True
    assert result.metric_extension_executed is False
    assert result.metric_extension_report_created is False
    assert result.extended_metric_result_rows_created is False
    assert result.extended_metric_summary_created is False
    assert result.extended_metrics_computed is False
    assert result.sample_row_count == 3
    assert result.eligible_sample_count == 3
    assert pd.read_csv(result.artifact_paths["result_rows"]).empty
    _assert_downstream_flags_false(result)


def test_happy_path_with_allow_computes_only_allowed_report_only_metrics(tmp_path: Path) -> None:
    result = run_metric_extension(replace(_happy_settings(tmp_path), allow_metric_extension=True))

    assert result.status == METRIC_EXTENSION_REPORT_CREATED
    assert result.workflow_stage == METRIC_EXTENSION_REPORT_CREATED
    assert result.ready_for_metric_extension is True
    assert result.metric_extension_executed is True
    assert result.metric_extension_report_created is True
    assert result.extended_metric_result_rows_created is True
    assert result.extended_metric_summary_created is True
    assert result.extended_metrics_computed is True
    assert result.benchmark_relative_return_created is True
    assert result.industry_relative_return_created is True
    assert result.sample_row_count == 3
    assert result.eligible_sample_count == 3
    assert result.benchmark_denominator_count == 3
    assert result.industry_denominator_count == 3
    _assert_downstream_flags_false(result)

    rows = pd.read_csv(result.artifact_paths["result_rows"], dtype={"symbol": "string"})
    assert set(rows["metric_name"]) == set(ALLOWED_EXTENSION_METRIC_SET)
    assert len(rows) == 6
    first_benchmark = rows[(rows["symbol"].astype(str) == "000001") & (rows["metric_name"] == "benchmark_relative_return")].iloc[0]
    first_industry = rows[(rows["symbol"].astype(str) == "000001") & (rows["metric_name"] == "industry_relative_return")].iloc[0]
    assert first_benchmark["metric_value"] == pytest.approx(0.10 - 0.03)
    assert first_industry["metric_value"] == pytest.approx(0.10 - 0.04)
    assert rows["source_metric_computation_run_id"].eq("metric_comp_ext").all()
    assert rows["source_metric_evaluation_planning_run_id"].eq("metric_eval_ext").all()
    assert rows["source_training_evaluation_run_id"].eq("train_eval_ext").all()
    assert rows["source_forward_return_label_run_id"].eq("label_ext").all()
    assert rows["source_replay_decision_freeze_run_id"].eq("freeze_ext").all()
    assert rows["split_role"].eq("test").all()
    assert rows["label_name"].eq("forward_return_5d").all()
    assert rows["horizon_trading_days"].eq(5).all()
    assert rows["report_only"].eq(True).all()
    assert rows["diagnostic_only"].eq(True).all()
    assert "000001" in set(rows["symbol"].astype(str))
    assert not (_forbidden_result_columns() & set(rows.columns))

    summary = pd.read_csv(result.artifact_paths["summary"])
    assert set(summary["metric_name"]) == set(ALLOWED_EXTENSION_METRIC_SET)
    report = result.artifact_paths["report"].read_text(encoding="utf-8")
    for phrase in [
        "report-only benchmark/industry relative metrics",
        "bounded sample",
        "not strategy validation",
        "not training_result",
        "not weights",
        "not model_version",
        "not thresholds",
        "not predictions",
        "not calibrated probabilities",
        "not feature importance",
        "not stock_profile",
        "not buy-review",
        "not paper approval",
        "not performance validation",
        "not trading",
    ]:
        assert phrase in report


def test_cli_no_input_and_happy_paths(tmp_path: Path) -> None:
    no_input = _run_cli(["metric-extension", "--output-dir", str(_output_dir(tmp_path))])
    assert "status: NO_METRIC_EXTENSION_INPUT" in no_input.stdout
    assert "extended_metrics_computed: False" in no_input.stdout
    assert "trading_allowed: False" in no_input.stdout

    settings = _happy_settings(tmp_path)
    no_allow = _run_cli(_cli_args(settings))
    allow = _run_cli([*_cli_args(settings), "--allow-metric-extension"])
    assert "status: READY_FOR_METRIC_EXTENSION" in no_allow.stdout
    assert "extended_metric_result_rows_created: False" in no_allow.stdout
    assert "status: METRIC_EXTENSION_REPORT_CREATED" in allow.stdout
    assert "extended_metric_result_rows_created: True" in allow.stdout
    assert "benchmark_relative_return_created: True" in allow.stdout
    assert "industry_relative_return_created: True" in allow.stdout
    assert "training_result_created: False" in allow.stdout


def test_metric_extension_artifact_view_cli_commands_are_added_for_this_phase() -> None:
    help_text = _run_cli(["--help"]).stdout
    assert "metric-extension" in help_text
    assert "metric-extension-index" in help_text
    assert "metric-extension-health" in help_text
    assert "metric-extension-status" in help_text
    assert not Path("docs/project_sources").exists()
    assert Path("docs/release_checkpoint_v1.48.0.md").exists()


def test_metric_extension_index_discovers_no_input_ready_and_report_created_artifacts(tmp_path: Path) -> None:
    no_input, ready, created = _three_metric_extension_runs(tmp_path)

    index = build_metric_extension_index(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "index")

    assert index.artifact_count == 3
    rows = {row["metric_extension_run_id"]: row for row in index.index_frame.to_dict("records")}
    assert rows[no_input.metric_extension_run_id]["status"] == NO_METRIC_EXTENSION_INPUT
    assert rows[ready.metric_extension_run_id]["status"] == READY_FOR_METRIC_EXTENSION
    created_row = rows[created.metric_extension_run_id]
    assert created_row["status"] == METRIC_EXTENSION_REPORT_CREATED
    assert created_row["source_metric_computation_run_id"] == "metric_comp_ext"
    assert created_row["source_metric_evaluation_planning_run_id"] == "metric_eval_ext"
    assert created_row["source_training_evaluation_run_id"] == "train_eval_ext"
    assert created_row["source_forward_return_label_run_id"] == "label_ext"
    assert created_row["source_replay_decision_freeze_run_id"] == "freeze_ext"
    assert created_row["sample_row_count"] == 3
    assert created_row["eligible_sample_count"] == 3
    assert created_row["benchmark_mapping_row_count"] == 3
    assert created_row["industry_mapping_row_count"] == 3
    assert created_row["benchmark_denominator_count"] == 3
    assert created_row["industry_denominator_count"] == 3
    assert bool(created_row["extended_metric_result_rows_created"]) is True
    assert bool(created_row["extended_metric_summary_created"]) is True
    assert bool(created_row["extended_metrics_computed"]) is True
    assert bool(created_row["benchmark_relative_return_created"]) is True
    assert bool(created_row["industry_relative_return_created"]) is True
    assert set(created_row["metric_names_present"].split(",")) == set(ALLOWED_EXTENSION_METRIC_SET)
    assert created_row["result_row_count"] == 6
    assert created_row["summary_row_count"] == 2
    for field in DOWNSTREAM_FALSE_FIELDS:
        if field in created_row:
            assert bool(created_row[field]) is False, field
    for path_field in [
        "input_index_path",
        "metric_definitions_used_path",
        "benchmark_mapping_used_path",
        "industry_mapping_used_path",
        "return_fields_used_path",
        "sample_scope_used_path",
        "denominator_rules_used_path",
        "result_rows_path",
        "summary_path",
        "safety_flags_path",
    ]:
        assert Path(created_row[path_field]).exists(), path_field


def test_metric_extension_health_passes_for_valid_no_input_ready_and_report_created_artifacts(tmp_path: Path) -> None:
    _three_metric_extension_runs(tmp_path)

    health = check_metric_extension_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "PASS"
    assert health.checked_artifact_count == 3
    assert health.error_count == 0


@pytest.mark.parametrize(
    ("mutation", "expected_issue"),
    [
        ("clear_report_created_result_rows", "REPORT_CREATED_WITHOUT_RESULT_ROWS"),
        ("clear_report_created_summary", "REPORT_CREATED_WITHOUT_SUMMARY"),
        ("ready_with_result_rows", "RESULT_ROWS_WITHOUT_REPORT_CREATED_STATUS"),
        ("report_created_computed_false", "REPORT_CREATED_EXTENDED_METRICS_COMPUTED_FALSE"),
        ("allowed_set_unsupported", "ALLOWED_EXTENSION_METRIC_SET_UNSUPPORTED"),
        ("unsupported_metric", "RESULT_ROW_UNSUPPORTED_METRIC_NAMES"),
        ("path_metric", "RESULT_ROW_PATH_METRIC_NAMES"),
        ("ic_metric", "RESULT_ROW_ANALYTIC_METRIC_NAMES"),
        ("cost_metric", "RESULT_ROW_COST_TRADING_METRIC_NAMES"),
        ("missing_lineage", "RESULT_ROW_LINEAGE_MISSING"),
        ("missing_comparator_id", "RESULT_ROW_BENCHMARK_INDUSTRY_ID_MISSING"),
        ("missing_counts", "RESULT_ROW_NUMERATOR_DENOMINATOR_MISSING"),
        ("missing_report_flags", "RESULT_ROW_REPORT_FLAGS_MISSING"),
        ("training_result_column", "RESULT_ROW_FORBIDDEN_COLUMNS"),
        ("model_column", "RESULT_ROW_FORBIDDEN_COLUMNS"),
        ("threshold_prediction_column", "RESULT_ROW_FORBIDDEN_COLUMNS"),
        ("stock_profile_column", "RESULT_ROW_FORBIDDEN_COLUMNS"),
        ("buy_review_column", "RESULT_ROW_FORBIDDEN_COLUMNS"),
        ("paper_column", "RESULT_ROW_FORBIDDEN_COLUMNS"),
        ("performance_column", "RESULT_ROW_FORBIDDEN_COLUMNS"),
        ("trading_column", "RESULT_ROW_FORBIDDEN_COLUMNS"),
        ("overclaim_report", "REPORT_OVERCLAIM_WORDING"),
    ],
)
def test_metric_extension_health_fails_for_invalid_artifact_boundaries(
    tmp_path: Path, mutation: str, expected_issue: str
) -> None:
    _, ready, created = _three_metric_extension_runs(tmp_path)
    _mutate_metric_extension_artifact(ready, created, mutation)

    health = check_metric_extension_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert expected_issue in set(health.health_frame["issue_code"])


@pytest.mark.parametrize("field", DOWNSTREAM_FALSE_FIELDS)
def test_metric_extension_health_fails_for_downstream_or_side_effect_flags(tmp_path: Path, field: str) -> None:
    _, _, created = _three_metric_extension_runs(tmp_path)
    _patch_json(created.artifact_paths["metadata"], {field: True})
    _patch_json(created.artifact_paths["safety_flags"], {field: True})

    health = check_metric_extension_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert f"{field.upper()}_UNEXPECTED" in set(health.health_frame["issue_code"])


def test_metric_extension_status_reports_no_input_ready_and_report_created_states(tmp_path: Path) -> None:
    no_input = run_metric_extension(MetricExtensionSettings(output_dir=_output_dir(tmp_path)))
    no_input_status = run_metric_extension_status(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "status_no_input")
    assert no_input_status.latest_metric_extension_run_id == no_input.metric_extension_run_id
    assert no_input_status.status == NO_METRIC_EXTENSION_INPUT
    assert no_input_status.health_status == "PASS"
    assert no_input_status.ready_for_metric_extension is False

    ready = run_metric_extension(replace(_happy_settings(tmp_path / "ready_status"), output_dir=_output_dir(tmp_path)))
    ready_status = run_metric_extension_status(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "status_ready")
    assert ready_status.latest_metric_extension_run_id == ready.metric_extension_run_id
    assert ready_status.status == READY_FOR_METRIC_EXTENSION
    assert ready_status.ready_for_metric_extension is True
    assert ready_status.extended_metrics_computed is False

    created = run_metric_extension(replace(_happy_settings(tmp_path / "created_status"), output_dir=_output_dir(tmp_path), allow_metric_extension=True))
    created_status = run_metric_extension_status(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "status_created")
    assert created_status.latest_metric_extension_run_id == created.metric_extension_run_id
    assert created_status.status == METRIC_EXTENSION_REPORT_CREATED
    assert created_status.workflow_stage == METRIC_EXTENSION_REPORT_CREATED
    assert created_status.health_status == "PASS"
    assert created_status.metric_extension_report_created is True
    assert created_status.result_row_count == 6
    assert set(created_status.metric_names_present.split(",")) == set(ALLOWED_EXTENSION_METRIC_SET)
    for phrase in [
        "report-only",
        "bounded sample",
        "benchmark/industry relative",
        "not strategy validation",
        "not training_result",
        "not weights",
        "not model_version",
        "not thresholds",
        "not predictions/probabilities/feature importance",
        "not stock_profile",
        "not buy-review",
        "not paper approval",
        "not performance validation",
        "not trading",
    ]:
        assert phrase in created_status.safety_statement


def test_metric_extension_artifact_view_cli_commands_work(tmp_path: Path) -> None:
    _three_metric_extension_runs(tmp_path)
    root = _output_dir(tmp_path)

    index = _run_cli(["metric-extension-index", "--root", str(root), "--output-dir", str(root / "index")])
    health = _run_cli(["metric-extension-health", "--root", str(root), "--output-dir", str(root / "health")])
    status = _run_cli(["metric-extension-status", "--root", str(root), "--output-dir", str(root / "status")])

    assert "artifact_count: 3" in index.stdout
    assert "status: PASS" in health.stdout
    assert "latest_metric_extension_run_id:" in status.stdout
    assert "METRIC_EXTENSION_REPORT_CREATED" in status.stdout


def test_research_status_includes_metric_extension_report_only_context(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    settings = replace(
        _happy_settings(tmp_path),
        output_dir=root / "manual_diagnostics" / "metric_extension_v0_1",
        allow_metric_extension=True,
    )
    created = run_metric_extension(settings)

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.metric_extension_workflow_implemented is True
    assert result.metric_extension_views_implemented is True
    assert result.latest_metric_extension_run_id == created.metric_extension_run_id
    assert result.latest_metric_extension_status == METRIC_EXTENSION_REPORT_CREATED
    assert result.latest_metric_extension_health_status == "PASS"
    assert result.latest_metric_extension_workflow_stage == METRIC_EXTENSION_REPORT_CREATED
    assert result.metric_extension_report_created is True
    assert result.extended_metric_result_rows_created is True
    assert result.extended_metric_summary_created is True
    assert result.extended_metrics_computed is True
    assert result.allowed_extension_metric_set == ",".join(ALLOWED_EXTENSION_METRIC_SET)
    assert set(result.metric_extension_metric_names_present.split(",")) == set(ALLOWED_EXTENSION_METRIC_SET)
    assert result.metric_extension_result_row_count == 6
    assert result.metric_extension_summary_row_count == 2
    assert result.training_allowed is False
    assert result.weights_trained is False
    assert result.training_result_created is False
    assert result.model_version_created is False
    assert result.thresholds_optimized is False
    assert result.predictions_created is False
    assert result.calibrated_probabilities_created is False
    assert result.feature_importance_created is False
    assert result.stock_profile_allowed is False
    assert result.active_stock_profile_exists is False
    assert result.stock_profile_created is False
    assert result.buy_review_allowed is False
    assert result.real_buy_review_eligible is False
    assert result.approved_for_paper is False
    assert result.strategy_performance_validated is False
    assert result.trading_allowed is False
    assert result.order_placed is False
    assert result.broker_api_called is False
    assert result.message_sent is False
    assert result.llm_api_called is False
    assert result.external_api_called is False
    assert result.cache_mutated is False
    assert result.data_raw_written is False
    assert result.data_processed_written is False
    assert result.data_cache_written is False
    assert result.current_candidates_run is False
    assert result.snapshot_built is False
    assert result.signal_semantics_changed is False
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.no_live_trading is True
    assert result.no_broker_api is True
    assert result.no_order_placement is True
    assert result.no_message_sent is True


def test_research_status_preserves_paper_priority_with_metric_extension_context(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports"
    settings = replace(
        _happy_settings(tmp_path),
        output_dir=root / "manual_diagnostics" / "metric_extension_v0_1",
        allow_metric_extension=True,
    )
    run_metric_extension(settings)
    _paper_workflow_status(
        root,
        status="WARN",
        workflow_stage="WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        expected_demo_warning_count=1,
        next_manual_action="Demo WATCH_ONLY paper workflow validated; no fills were supplied.",
    )

    result = run_local_research_dashboard(root=root, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.latest_metric_extension_status == METRIC_EXTENSION_REPORT_CREATED
    row = result.dashboard_frame.loc[result.dashboard_frame["component"] == "METRIC_EXTENSION_STATUS"].iloc[0]
    assert row["warning_classification"] == ""


def test_metric_extension_research_status_docs_checkpoint_and_source_note_are_report_only() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    required_paths = [
        repo_root / "README.md",
        repo_root / "docs" / "local_research_dashboard.md",
        repo_root / "docs" / "metric_extension.md",
        repo_root / "docs" / "release_checkpoint_v1.48.0.md",
        repo_root / "SOURCE_UPDATE_NOTES_v1_48_0.md",
    ]

    for path in required_paths:
        assert path.exists(), path

    combined = "\n".join(path.read_text(encoding="utf-8") for path in required_paths)
    assert "metric-extension" in combined
    assert "research-status" in combined
    assert "PAPER_WORKFLOW_READY" in combined
    assert "report-only" in combined
    assert "not performance validation" in combined
    assert "not a training result" in combined
    assert "does not create weights" in combined
    assert "does not create model versions" in combined
    assert "does not create thresholds" in combined
    assert "does not create predictions or probabilities" in combined
    assert "does not create feature importance" in combined
    assert "does not create stock profiles" in combined
    assert "does not create buy-review eligibility" in combined
    assert "does not approve paper trading" in combined
    assert "does not allow live trading" in combined
    assert "does not call broker APIs" in combined
    assert "does not place orders" in combined
    assert "does not send messages" in combined
    assert "Project Source should be refreshed after commit and tag" in combined
    assert not (repo_root / "docs" / "project_sources").exists()


def _happy_settings(tmp_path: Path) -> MetricExtensionSettings:
    root = tmp_path / "fixtures"
    root.mkdir(parents=True, exist_ok=True)
    metric_dir = root / "metric_computation"
    metric_dir.mkdir()
    metric_metadata = _write_json(metric_dir / "metric_computation_metadata.json", _metric_computation_metadata())
    metric_rows = _write_csv(metric_dir / "metric_computation_result_rows.csv", _metric_computation_result_rows())
    metric_summary = _write_csv(metric_dir / "metric_computation_summary.csv", [{"metric_name": "average_return", "metric_value": 0.08}])
    metric_safety = _write_json(metric_dir / "metric_computation_safety_flags.json", _safe_flags())
    metric_status = _write_json(metric_dir / "metric_computation_status.json", {"status": "METRIC_COMPUTATION_REPORT_CREATED"})
    metric_health = _write_json(metric_dir / "metric_computation_health.json", {"status": "PASS"})

    metric_eval_dir = root / "metric_evaluation"
    metric_eval_dir.mkdir()
    metric_eval_metadata = _write_json(metric_eval_dir / "metric_evaluation_metadata.json", _metric_evaluation_metadata())
    metric_eval_index = _write_csv(metric_eval_dir / "metric_evaluation_input_index.csv", [{"input_component": "sample_rows", "source_hash_coverage": "PASS", "revision_id_coverage": "PASS", "available_time_coverage": "PASS", "quality_status_coverage": "PASS"}])
    sample_scope = _write_csv(metric_eval_dir / "metric_evaluation_sample_scope.csv", [{"valid_sample_scope": True, "report_only": True, "diagnostic_only": True}])
    denominator_rules = _write_csv(metric_eval_dir / "metric_evaluation_denominator_rules.csv", _denominator_rules())
    metric_eval_safety = _write_json(metric_eval_dir / "metric_evaluation_safety_flags.json", _safe_flags())
    metric_eval_status = _write_json(metric_eval_dir / "metric_evaluation_status.json", {"status": "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED"})
    metric_eval_health = _write_json(metric_eval_dir / "metric_evaluation_health.json", {"status": "PASS"})

    train_dir = root / "training_evaluation"
    train_dir.mkdir()
    training_metadata = _write_json(train_dir / "training_evaluation_metadata.json", _training_metadata())
    sample_rows = _write_csv(train_dir / "training_evaluation_sample_rows.csv", _sample_rows())
    training_safety = _write_json(train_dir / "training_evaluation_safety_flags.json", _safe_flags())
    training_status = _write_json(train_dir / "training_evaluation_status.json", {"status": "TRAINING_EVALUATION_DATASET_CREATED"})
    training_health = _write_json(train_dir / "training_evaluation_health.json", {"status": "PASS"})

    label_dir = root / "forward_return_label"
    label_dir.mkdir()
    label_metadata = _write_json(label_dir / "forward_return_label_metadata.json", _forward_label_metadata())
    label_rows = _write_csv(label_dir / "forward_return_label_rows.csv", [{"forward_return_label_id": row["forward_return_label_id"], "report_only": True, "diagnostic_only": True} for row in _sample_rows()])
    label_status = _write_json(label_dir / "forward_return_label_status.json", {"status": "FORWARD_RETURN_LABELS_CREATED"})
    label_health = _write_json(label_dir / "forward_return_label_health.json", {"status": "PASS"})

    freeze_dir = root / "replay_decision_freeze"
    freeze_dir.mkdir()
    freeze_metadata = _write_json(freeze_dir / "replay_decision_freeze_metadata.json", _replay_freeze_metadata())
    freeze_rows = _write_csv(freeze_dir / "replay_decision_freeze_rows.csv", [{"replay_decision_id": row["replay_decision_id"], "report_only": True, "diagnostic_only": True} for row in _sample_rows()])
    freeze_status = _write_json(freeze_dir / "replay_decision_freeze_status.json", {"status": "REPLAY_DECISION_FROZEN"})
    freeze_health = _write_json(freeze_dir / "replay_decision_freeze_health.json", {"status": "PASS"})

    benchmark_mapping = _write_csv(root / "benchmark_mapping.csv", _benchmark_rows())
    industry_mapping = _write_csv(root / "industry_mapping.csv", _industry_rows())

    return MetricExtensionSettings(
        approval_manifest_path=_write_json(root / "approval.json", {"approval_text": EXACT_METRIC_EXTENSION_APPROVAL_TEXT}),
        metric_extension_request_manifest_path=_write_json(root / "request.json", {"requested_extension_metric_set": list(ALLOWED_EXTENSION_METRIC_SET)}),
        metric_computation_metadata_path=metric_metadata,
        metric_computation_result_rows_path=metric_rows,
        metric_computation_summary_path=metric_summary,
        metric_computation_safety_flags_path=metric_safety,
        metric_computation_status_artifact_path=metric_status,
        metric_computation_health_artifact_path=metric_health,
        metric_evaluation_metadata_path=metric_eval_metadata,
        metric_evaluation_input_index_path=metric_eval_index,
        metric_evaluation_sample_scope_path=sample_scope,
        metric_evaluation_denominator_rules_path=denominator_rules,
        metric_evaluation_safety_flags_path=metric_eval_safety,
        metric_evaluation_status_artifact_path=metric_eval_status,
        metric_evaluation_health_artifact_path=metric_eval_health,
        training_evaluation_metadata_path=training_metadata,
        training_evaluation_sample_rows_path=sample_rows,
        training_evaluation_safety_flags_path=training_safety,
        training_evaluation_status_artifact_path=training_status,
        training_evaluation_health_artifact_path=training_health,
        forward_return_label_metadata_path=label_metadata,
        forward_return_label_rows_path=label_rows,
        forward_return_label_status_artifact_path=label_status,
        forward_return_label_health_artifact_path=label_health,
        replay_decision_freeze_metadata_path=freeze_metadata,
        replay_decision_freeze_rows_path=freeze_rows,
        replay_decision_freeze_status_artifact_path=freeze_status,
        replay_decision_freeze_health_artifact_path=freeze_health,
        benchmark_mapping_path=benchmark_mapping,
        industry_mapping_path=industry_mapping,
        benchmark_return_rows_path=benchmark_mapping,
        industry_return_rows_path=industry_mapping,
        leakage_evidence_bundle_path=_write_json(root / "leakage.json", {"future_label_leakage": False, "training_leakage": False}),
        overclaim_evidence_bundle_path=_write_json(root / "overclaim.json", _overclaim_flags()),
        side_effect_evidence_bundle_path=_write_json(root / "side_effect.json", _safe_flags()),
        output_dir=_output_dir(tmp_path),
    )


def _metric_computation_metadata() -> dict[str, object]:
    return {
        "metric_computation_run_id": "metric_comp_ext",
        "status": "METRIC_COMPUTATION_REPORT_CREATED",
        "execution_status": "METRIC_COMPUTATION_REPORT_CREATED",
        "workflow_stage": "METRIC_COMPUTATION_REPORT_CREATED",
        "metric_computation_report_created": True,
        "metrics_computed": True,
        "health_status": "PASS",
        "source_metric_evaluation_planning_run_id": "metric_eval_ext",
        "source_training_evaluation_run_id": "train_eval_ext",
        "source_forward_return_label_run_id": "label_ext",
        "source_replay_decision_freeze_run_id": "freeze_ext",
        "report_only": True,
        "diagnostic_only": True,
    } | _safe_flags()


def _metric_evaluation_metadata() -> dict[str, object]:
    return {
        "metric_evaluation_run_id": "metric_eval_ext",
        "status": "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED",
        "execution_status": "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED",
        "workflow_stage": "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED",
        "health_status": "PASS",
        "source_training_evaluation_run_id": "train_eval_ext",
        "source_forward_return_label_run_id": "label_ext",
        "source_replay_decision_freeze_run_id": "freeze_ext",
        "report_only": True,
        "diagnostic_only": True,
    } | _safe_flags()


def _training_metadata() -> dict[str, object]:
    return {
        "training_evaluation_run_id": "train_eval_ext",
        "status": "TRAINING_EVALUATION_DATASET_CREATED",
        "execution_status": "TRAINING_EVALUATION_DATASET_CREATED",
        "workflow_stage": "TRAINING_EVALUATION_DATASET_CREATED",
        "health_status": "PASS",
        "source_forward_return_label_run_id": "label_ext",
        "source_replay_decision_freeze_run_id": "freeze_ext",
        "training_evaluation_dataset_artifacts_created": True,
        "report_only": True,
        "diagnostic_only": True,
    } | _safe_flags()


def _forward_label_metadata() -> dict[str, object]:
    return {"forward_return_label_run_id": "label_ext", "status": "FORWARD_RETURN_LABELS_CREATED", "execution_status": "FORWARD_RETURN_LABELS_CREATED", "health_status": "PASS", "report_only": True, "diagnostic_only": True}


def _replay_freeze_metadata() -> dict[str, object]:
    return {"replay_decision_freeze_run_id": "freeze_ext", "status": "REPLAY_DECISION_FROZEN", "execution_status": "REPLAY_DECISION_FROZEN", "health_status": "PASS", "report_only": True, "diagnostic_only": True}


def _sample_rows() -> list[dict[str, object]]:
    base = {
        "metric_computation_run_id": "metric_comp_ext",
        "metric_evaluation_run_id": "metric_eval_ext",
        "training_evaluation_run_id": "train_eval_ext",
        "replay_decision_freeze_run_id": "freeze_ext",
        "forward_return_label_run_id": "label_ext",
        "replay_as_of_date": "2024-04-02",
        "split_role": "test",
        "label_name": "forward_return_5d",
        "horizon_trading_days": 5,
        "source_hash_coverage": "PASS",
        "revision_id_coverage": "PASS",
        "available_time_coverage": "PASS",
        "quality_status_coverage": "PASS",
        "report_only": True,
        "diagnostic_only": True,
    }
    return [
        {
            **base,
            "training_evaluation_sample_id": "sample_001",
            "metric_computation_result_row_id": "metric_row_001",
            "replay_decision_id": "decision_000001_20240402",
            "forward_return_label_id": "label_001",
            "symbol": "000001",
            "label_value": 0.10,
        },
        {
            **base,
            "training_evaluation_sample_id": "sample_002",
            "metric_computation_result_row_id": "metric_row_002",
            "replay_decision_id": "decision_000002_20240402",
            "forward_return_label_id": "label_002",
            "symbol": "000002",
            "label_value": -0.05,
        },
        {
            **base,
            "training_evaluation_sample_id": "sample_003",
            "metric_computation_result_row_id": "metric_row_003",
            "replay_decision_id": "decision_159915_20240402",
            "forward_return_label_id": "label_003",
            "symbol": "159915",
            "label_value": 0.20,
        },
    ]


def _metric_computation_result_rows() -> list[dict[str, object]]:
    return [
        {
            "metric_computation_run_id": "metric_comp_ext",
            "source_metric_evaluation_planning_run_id": "metric_eval_ext",
            "source_training_evaluation_run_id": "train_eval_ext",
            "metric_name": "average_return",
            "metric_value": 0.08,
            "report_only": True,
            "diagnostic_only": True,
        }
    ]


def _benchmark_rows() -> list[dict[str, object]]:
    returns = {"000001": 0.03, "000002": -0.01, "159915": 0.05}
    return [
        {
            "symbol": symbol,
            "replay_as_of_date": "2024-04-02",
            "horizon_trading_days": 5,
            "benchmark_id": "CSI300",
            "benchmark_name": "CSI 300",
            "benchmark_return_value": value,
            "benchmark_available_time": "2024-04-02T16:00:00",
            "benchmark_source_hash": f"bench_hash_{symbol}",
            "benchmark_revision_id": "bench_rev_1",
            "benchmark_quality_status": "PASS",
            "benchmark_denominator_eligible": True,
            "report_only": True,
            "diagnostic_only": True,
        }
        for symbol, value in returns.items()
    ]


def _industry_rows() -> list[dict[str, object]]:
    returns = {"000001": 0.04, "000002": -0.02, "159915": 0.06}
    return [
        {
            "symbol": symbol,
            "replay_as_of_date": "2024-04-02",
            "horizon_trading_days": 5,
            "industry_id": "bank" if symbol != "159915" else "etf",
            "industry_name": "Bank" if symbol != "159915" else "ETF",
            "industry_return_value": value,
            "industry_classification_available_time": "2024-04-02T16:00:00",
            "industry_return_available_time": "2024-04-02T16:00:00",
            "industry_source_hash": f"industry_hash_{symbol}",
            "industry_revision_id": "industry_rev_1",
            "industry_quality_status": "PASS",
            "industry_denominator_eligible": True,
            "report_only": True,
            "diagnostic_only": True,
        }
        for symbol, value in returns.items()
    ]


def _denominator_rules() -> list[dict[str, object]]:
    return [
        {
            "metric_name": metric,
            "denominator_scope": "eligible rows with numeric label and comparator return",
            "include_condition": "complete lineage and quality PASS",
            "exclude_condition": "missing or non-numeric comparator",
            "report_only": True,
            "diagnostic_only": True,
        }
        for metric in ALLOWED_EXTENSION_METRIC_SET
    ]


def _safe_flags() -> dict[str, object]:
    return {field: False for field in DOWNSTREAM_FALSE_FIELDS} | {"report_only": True, "diagnostic_only": True}


def _overclaim_flags() -> dict[str, object]:
    return {
        "metric_extension_not_strategy_validation": True,
        "metric_extension_not_training_result": True,
        "metric_extension_not_weights": True,
        "metric_extension_not_model_version": True,
        "metric_extension_not_thresholds": True,
        "metric_extension_not_predictions": True,
        "metric_extension_not_probabilities": True,
        "metric_extension_not_feature_importance": True,
        "metric_extension_not_stock_profile": True,
        "metric_extension_not_buy_review": True,
        "metric_extension_not_paper_approval": True,
        "metric_extension_not_performance_validation": True,
        "metric_extension_not_trading": True,
    }


def _three_metric_extension_runs(tmp_path: Path):
    no_input = run_metric_extension(MetricExtensionSettings(output_dir=_output_dir(tmp_path)))
    ready = run_metric_extension(replace(_happy_settings(tmp_path / "ready"), output_dir=_output_dir(tmp_path)))
    created = run_metric_extension(replace(_happy_settings(tmp_path / "created"), output_dir=_output_dir(tmp_path), allow_metric_extension=True))
    return no_input, ready, created


def _mutate_metric_extension_artifact(ready: object, created: object, mutation: str) -> None:
    created_result_rows_path = created.artifact_paths["result_rows"]
    created_summary_path = created.artifact_paths["summary"]
    rows = pd.read_csv(created_result_rows_path, dtype={"symbol": "string"})

    if mutation == "clear_report_created_result_rows":
        pd.DataFrame(columns=rows.columns).to_csv(created_result_rows_path, index=False)
    elif mutation == "clear_report_created_summary":
        pd.DataFrame(columns=pd.read_csv(created_summary_path).columns).to_csv(created_summary_path, index=False)
    elif mutation == "ready_with_result_rows":
        rows.to_csv(ready.artifact_paths["result_rows"], index=False)
    elif mutation == "report_created_computed_false":
        _patch_json(created.artifact_paths["metadata"], {"extended_metrics_computed": False})
        _patch_json(created.artifact_paths["safety_flags"], {"extended_metrics_computed": False})
    elif mutation == "allowed_set_unsupported":
        _patch_json(created.artifact_paths["metadata"], {"allowed_extension_metric_set": "benchmark_relative_return,max_drawdown"})
    elif mutation == "unsupported_metric":
        rows.loc[0, "metric_name"] = "unsupported_metric"
        rows.to_csv(created_result_rows_path, index=False)
    elif mutation == "path_metric":
        rows.loc[0, "metric_name"] = "max_drawdown"
        rows.to_csv(created_result_rows_path, index=False)
    elif mutation == "ic_metric":
        rows.loc[0, "metric_name"] = "information_coefficient"
        rows.to_csv(created_result_rows_path, index=False)
    elif mutation == "cost_metric":
        rows.loc[0, "metric_name"] = "turnover"
        rows.to_csv(created_result_rows_path, index=False)
    elif mutation == "missing_lineage":
        rows.loc[0, "source_metric_computation_run_id"] = ""
        rows.to_csv(created_result_rows_path, index=False)
    elif mutation == "missing_comparator_id":
        rows.loc[rows["metric_name"] == "benchmark_relative_return", "benchmark_id"] = ""
        rows.to_csv(created_result_rows_path, index=False)
    elif mutation == "missing_counts":
        rows.loc[0, "denominator_count"] = ""
        rows.to_csv(created_result_rows_path, index=False)
    elif mutation == "missing_report_flags":
        rows.loc[0, "report_only"] = False
        rows.to_csv(created_result_rows_path, index=False)
    elif mutation == "training_result_column":
        rows["training_result"] = "blocked"
        rows.to_csv(created_result_rows_path, index=False)
    elif mutation == "model_column":
        rows["model_version"] = "blocked"
        rows.to_csv(created_result_rows_path, index=False)
    elif mutation == "threshold_prediction_column":
        rows["prediction"] = 0.1
        rows.to_csv(created_result_rows_path, index=False)
    elif mutation == "stock_profile_column":
        rows["stock_profile_status"] = "blocked"
        rows.to_csv(created_result_rows_path, index=False)
    elif mutation == "buy_review_column":
        rows["real_buy_review_eligible"] = True
        rows.to_csv(created_result_rows_path, index=False)
    elif mutation == "paper_column":
        rows["approved_for_paper"] = True
        rows.to_csv(created_result_rows_path, index=False)
    elif mutation == "performance_column":
        rows["strategy_performance_validated"] = True
        rows.to_csv(created_result_rows_path, index=False)
    elif mutation == "trading_column":
        rows["order_id"] = "blocked"
        rows.to_csv(created_result_rows_path, index=False)
    elif mutation == "overclaim_report":
        created.artifact_paths["report"].write_text("This report grants trading permission.", encoding="utf-8")
    else:
        raise AssertionError(f"Unknown mutation: {mutation}")


def _paper_workflow_status(
    root: Path,
    *,
    workflow_status_id: str = "paper-workflow-status-a",
    status: str = "PASS",
    workflow_stage: str = "WORKFLOW_COMPLETE",
    expected_demo_warning_count: int = 0,
    next_manual_action: str = "Review completed workflow artifacts.",
) -> Path:
    folder = root / "paper_trading" / "workflow_status" / workflow_status_id
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "paper_workflow_status_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    _write_json(
        folder / "metadata.json",
        {
            "workflow_status_id": workflow_status_id,
            "created_at": "2024-04-02T16:15:00",
            "status": status,
            "workflow_stage": workflow_stage,
            "latest_decision_date": "2024-04-02",
            "next_manual_action": next_manual_action,
            "total_warning_count": expected_demo_warning_count,
            "expected_demo_warning_count": expected_demo_warning_count,
            "stale_warning_count": 0,
            "actionable_warning_count": 0,
            "blocking_error_count": 0,
            "component_statuses": {
                "total_warning_count": expected_demo_warning_count,
                "expected_demo_warning_count": expected_demo_warning_count,
                "stale_warning_count": 0,
                "actionable_warning_count": 0,
                "blocking_error_count": 0,
            },
            "output_files": {"paper_workflow_status_report": str(report)},
            "warnings": [],
            "live_trading_enabled": False,
            "broker_api_invoked": False,
        },
    )
    return folder


def _required_artifact_keys() -> list[str]:
    return [
        "metadata",
        "report",
        "input_index",
        "metric_definitions_used",
        "benchmark_mapping_used",
        "industry_mapping_used",
        "return_fields_used",
        "sample_scope_used",
        "denominator_rules_used",
        "result_rows",
        "summary",
        "safety_flags",
        "precondition_results",
        "approval_results",
        "input_lineage_results",
        "metric_definition_results",
        "benchmark_mapping_results",
        "industry_mapping_results",
        "return_field_results",
        "denominator_results",
        "sample_scope_results",
        "result_row_results",
        "leakage_guard_results",
        "side_effect_guard_results",
        "overclaim_guard_results",
        "recommended_next_task",
    ]


def _forbidden_result_columns() -> set[str]:
    return {
        "training_result",
        "model_weight",
        "model_version",
        "threshold_optimized",
        "prediction",
        "calibrated_probability",
        "feature_importance",
        "stock_profile_status",
        "stock_profile_validated",
        "real_buy_review_eligible",
        "approved_for_paper",
        "strategy_performance_validated",
        "order_id",
        "broker_order_id",
        "trade_id",
    }


def _assert_downstream_flags_false(result: object) -> None:
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert getattr(result, field) is False, field


def _cli_args(settings: MetricExtensionSettings) -> list[str]:
    args = ["metric-extension"]
    for flag, value in [
        ("--approval-manifest-path", settings.approval_manifest_path),
        ("--metric-extension-request-manifest-path", settings.metric_extension_request_manifest_path),
        ("--metric-computation-metadata-path", settings.metric_computation_metadata_path),
        ("--metric-computation-result-rows-path", settings.metric_computation_result_rows_path),
        ("--metric-computation-summary-path", settings.metric_computation_summary_path),
        ("--metric-computation-safety-flags-path", settings.metric_computation_safety_flags_path),
        ("--metric-computation-status-artifact-path", settings.metric_computation_status_artifact_path),
        ("--metric-computation-health-artifact-path", settings.metric_computation_health_artifact_path),
        ("--metric-evaluation-metadata-path", settings.metric_evaluation_metadata_path),
        ("--metric-evaluation-input-index-path", settings.metric_evaluation_input_index_path),
        ("--metric-evaluation-sample-scope-path", settings.metric_evaluation_sample_scope_path),
        ("--metric-evaluation-denominator-rules-path", settings.metric_evaluation_denominator_rules_path),
        ("--metric-evaluation-safety-flags-path", settings.metric_evaluation_safety_flags_path),
        ("--metric-evaluation-status-artifact-path", settings.metric_evaluation_status_artifact_path),
        ("--metric-evaluation-health-artifact-path", settings.metric_evaluation_health_artifact_path),
        ("--training-evaluation-metadata-path", settings.training_evaluation_metadata_path),
        ("--training-evaluation-sample-rows-path", settings.training_evaluation_sample_rows_path),
        ("--training-evaluation-safety-flags-path", settings.training_evaluation_safety_flags_path),
        ("--training-evaluation-status-artifact-path", settings.training_evaluation_status_artifact_path),
        ("--training-evaluation-health-artifact-path", settings.training_evaluation_health_artifact_path),
        ("--forward-return-label-metadata-path", settings.forward_return_label_metadata_path),
        ("--forward-return-label-rows-path", settings.forward_return_label_rows_path),
        ("--forward-return-label-status-artifact-path", settings.forward_return_label_status_artifact_path),
        ("--forward-return-label-health-artifact-path", settings.forward_return_label_health_artifact_path),
        ("--replay-decision-freeze-metadata-path", settings.replay_decision_freeze_metadata_path),
        ("--replay-decision-freeze-rows-path", settings.replay_decision_freeze_rows_path),
        ("--replay-decision-freeze-status-artifact-path", settings.replay_decision_freeze_status_artifact_path),
        ("--replay-decision-freeze-health-artifact-path", settings.replay_decision_freeze_health_artifact_path),
        ("--benchmark-mapping-path", settings.benchmark_mapping_path),
        ("--industry-mapping-path", settings.industry_mapping_path),
        ("--benchmark-return-rows-path", settings.benchmark_return_rows_path),
        ("--industry-return-rows-path", settings.industry_return_rows_path),
        ("--leakage-evidence-bundle-path", settings.leakage_evidence_bundle_path),
        ("--overclaim-evidence-bundle-path", settings.overclaim_evidence_bundle_path),
        ("--side-effect-evidence-bundle-path", settings.side_effect_evidence_bundle_path),
        ("--output-dir", settings.output_dir),
    ]:
        if value is not None:
            args.extend([flag, str(value)])
    return args


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", *args],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
        cwd=Path(__file__).resolve().parents[1],
    )


def _write_json(path: Path | None, payload: dict[str, object]) -> Path:
    assert path is not None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _patch_json(path: Path | None, patch: dict[str, object]) -> None:
    assert path is not None
    payload = _read_json(path)
    payload.update(patch)
    _write_json(path, payload)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "metric_extension_v0_1"
