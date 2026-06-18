from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.metric_computation import (
    ALLOWED_METRIC_SET,
    EXACT_METRIC_COMPUTATION_APPROVAL_TEXT,
    METRIC_COMPUTATION_APPROVAL_BLOCKED,
    METRIC_COMPUTATION_DATASET_INPUT_BLOCKED,
    METRIC_COMPUTATION_DENOMINATOR_BLOCKED,
    METRIC_COMPUTATION_HEALTH_BLOCKED,
    METRIC_COMPUTATION_LEAKAGE_BLOCKED,
    METRIC_COMPUTATION_LINEAGE_BLOCKED,
    METRIC_COMPUTATION_OVERCLAIM_BLOCKED,
    METRIC_COMPUTATION_PLANNING_INPUT_BLOCKED,
    METRIC_COMPUTATION_REPORT_CREATED,
    METRIC_COMPUTATION_SAMPLE_SCOPE_BLOCKED,
    METRIC_COMPUTATION_SIDE_EFFECT_BLOCKED,
    METRIC_COMPUTATION_UNSUPPORTED_METRIC_BLOCKED,
    NO_METRIC_COMPUTATION_INPUT,
    READY_FOR_METRIC_COMPUTATION,
    MetricComputationSettings,
    run_metric_computation,
)
from quant_replay_system.metric_evaluation import run_metric_evaluation
from test_metric_evaluation import _happy_settings as _metric_evaluation_happy_settings


def test_no_input_writes_required_artifacts_with_safe_defaults(tmp_path: Path) -> None:
    result = run_metric_computation(MetricComputationSettings(output_dir=_output_dir(tmp_path)))

    assert result.status == NO_METRIC_COMPUTATION_INPUT
    assert result.workflow_stage == "METRIC_COMPUTATION_NO_INPUT"
    assert result.ready_for_metric_computation is False
    assert result.metric_computation_executed is False
    assert result.metric_computation_report_created is False
    assert result.metric_result_rows_created is False
    assert result.metric_summary_created is False
    assert result.metrics_computed is False
    assert result.allowed_metric_set == ",".join(ALLOWED_METRIC_SET)
    assert result.unsupported_metrics_requested is False
    assert result.sample_row_count == 0
    assert result.eligible_sample_count == 0
    assert result.quarantined_sample_count == 0
    assert result.label_coverage_numerator == 0
    assert result.label_coverage_denominator == 0
    _assert_downstream_flags_false(result)
    for key in _required_artifact_keys():
        assert result.artifact_paths[key].exists(), key
    metadata = _read_json(result.artifact_paths["metadata"])
    safety = _read_json(result.artifact_paths["safety_flags"])
    assert metadata["execution_status"] == NO_METRIC_COMPUTATION_INPUT
    assert metadata["ready_for_metric_computation"] is False
    assert metadata["metrics_computed"] is False
    assert safety["metrics_computed"] is False
    assert pd.read_csv(result.artifact_paths["result_rows"]).empty
    assert pd.read_csv(result.artifact_paths["summary"]).empty


@pytest.mark.parametrize(
    "approval_text",
    ["", "continue", "go ahead", "do the next task", "compute metrics", "run evaluation", "train the model"],
)
def test_vague_or_missing_approval_blocks(tmp_path: Path, approval_text: str) -> None:
    settings = _happy_settings(tmp_path)
    _write_json(settings.approval_manifest_path, {"approval_text": approval_text})

    result = run_metric_computation(settings)

    assert result.status == METRIC_COMPUTATION_APPROVAL_BLOCKED
    assert result.ready_for_metric_computation is False
    assert result.metrics_computed is False
    assert result.metric_result_rows_created is False
    _assert_downstream_flags_false(result)


@pytest.mark.parametrize(
    "request_patch",
    [
        {"requested_metric_set": ["sample_count", "benchmark_relative_return"]},
        {"requested_metric_set": ["industry_relative_return"]},
        {"requested_metric_set": ["max_drawdown"]},
        {"requested_metric_set": ["information_coefficient"]},
    ],
)
def test_unsupported_or_advanced_metrics_block(tmp_path: Path, request_patch: dict[str, object]) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.metric_computation_request_manifest_path, request_patch)

    result = run_metric_computation(settings)

    assert result.status == METRIC_COMPUTATION_UNSUPPORTED_METRIC_BLOCKED
    assert result.unsupported_metrics_requested is True
    assert result.metrics_computed is False


@pytest.mark.parametrize(
    ("request_patch", "expected_status"),
    [
        ({"training_result_requested": True}, METRIC_COMPUTATION_OVERCLAIM_BLOCKED),
        ({"weights_requested": True}, METRIC_COMPUTATION_OVERCLAIM_BLOCKED),
        ({"model_version_requested": True}, METRIC_COMPUTATION_OVERCLAIM_BLOCKED),
        ({"thresholds_requested": True}, METRIC_COMPUTATION_OVERCLAIM_BLOCKED),
        ({"predictions_requested": True}, METRIC_COMPUTATION_OVERCLAIM_BLOCKED),
        ({"calibrated_probabilities_requested": True}, METRIC_COMPUTATION_OVERCLAIM_BLOCKED),
        ({"feature_importance_requested": True}, METRIC_COMPUTATION_OVERCLAIM_BLOCKED),
        ({"stock_profile_requested": True}, METRIC_COMPUTATION_OVERCLAIM_BLOCKED),
        ({"buy_review_requested": True}, METRIC_COMPUTATION_OVERCLAIM_BLOCKED),
        ({"paper_approval_requested": True}, METRIC_COMPUTATION_OVERCLAIM_BLOCKED),
        ({"performance_validation_requested": True}, METRIC_COMPUTATION_OVERCLAIM_BLOCKED),
        ({"trading_requested": True}, METRIC_COMPUTATION_SIDE_EFFECT_BLOCKED),
    ],
)
def test_downstream_scope_requests_block(
    tmp_path: Path,
    request_patch: dict[str, object],
    expected_status: str,
) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.metric_computation_request_manifest_path, request_patch)

    result = run_metric_computation(settings)

    assert result.status == expected_status
    assert result.metric_computation_report_created is False
    _assert_downstream_flags_false(result)


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("metric_evaluation_metadata_path", METRIC_COMPUTATION_PLANNING_INPUT_BLOCKED),
        ("metric_evaluation_input_index_path", METRIC_COMPUTATION_PLANNING_INPUT_BLOCKED),
        ("metric_evaluation_metric_definitions_path", METRIC_COMPUTATION_PLANNING_INPUT_BLOCKED),
        ("metric_evaluation_sample_scope_path", METRIC_COMPUTATION_SAMPLE_SCOPE_BLOCKED),
        ("metric_evaluation_denominator_rules_path", METRIC_COMPUTATION_DENOMINATOR_BLOCKED),
        ("metric_evaluation_safety_flags_path", METRIC_COMPUTATION_PLANNING_INPUT_BLOCKED),
        ("metric_evaluation_health_artifact_path", METRIC_COMPUTATION_HEALTH_BLOCKED),
        ("training_evaluation_metadata_path", METRIC_COMPUTATION_DATASET_INPUT_BLOCKED),
        ("training_evaluation_sample_rows_path", METRIC_COMPUTATION_DATASET_INPUT_BLOCKED),
        ("training_evaluation_label_coverage_report_path", METRIC_COMPUTATION_DATASET_INPUT_BLOCKED),
        ("training_evaluation_safety_flags_path", METRIC_COMPUTATION_DATASET_INPUT_BLOCKED),
        ("training_evaluation_health_artifact_path", METRIC_COMPUTATION_HEALTH_BLOCKED),
        ("leakage_evidence_bundle_path", METRIC_COMPUTATION_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", METRIC_COMPUTATION_OVERCLAIM_BLOCKED),
        ("side_effect_evidence_bundle_path", METRIC_COMPUTATION_SIDE_EFFECT_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(
    tmp_path: Path,
    setting_name: str,
    expected_status: str,
) -> None:
    result = run_metric_computation(replace(_happy_settings(tmp_path), **{setting_name: None}))

    assert result.status == expected_status
    assert result.metrics_computed is False


@pytest.mark.parametrize(
    ("path_name", "patch", "expected_status"),
    [
        ("metric_evaluation_metadata_path", {"status": "NO_METRIC_EVALUATION_INPUT"}, METRIC_COMPUTATION_PLANNING_INPUT_BLOCKED),
        ("metric_evaluation_metadata_path", {"metric_evaluation_planning_artifacts_created": False}, METRIC_COMPUTATION_PLANNING_INPUT_BLOCKED),
        ("metric_evaluation_health_artifact_path", {"status": "FAIL"}, METRIC_COMPUTATION_HEALTH_BLOCKED),
        ("training_evaluation_metadata_path", {"status": "NO_TRAINING_EVALUATION_INPUT"}, METRIC_COMPUTATION_DATASET_INPUT_BLOCKED),
        ("training_evaluation_metadata_path", {"training_evaluation_dataset_artifacts_created": False}, METRIC_COMPUTATION_DATASET_INPUT_BLOCKED),
        ("training_evaluation_metadata_path", {"source_replay_decision_freeze_run_id": ""}, METRIC_COMPUTATION_LINEAGE_BLOCKED),
        ("training_evaluation_metadata_path", {"source_forward_return_label_run_id": ""}, METRIC_COMPUTATION_LINEAGE_BLOCKED),
        ("training_evaluation_health_artifact_path", {"status": "FAIL"}, METRIC_COMPUTATION_HEALTH_BLOCKED),
        ("leakage_evidence_bundle_path", {"future_label_leakage": True}, METRIC_COMPUTATION_LEAKAGE_BLOCKED),
        ("side_effect_evidence_bundle_path", {"broker_api_called": True}, METRIC_COMPUTATION_SIDE_EFFECT_BLOCKED),
        ("overclaim_evidence_bundle_path", {"metric_computation_not_performance_validation": False}, METRIC_COMPUTATION_OVERCLAIM_BLOCKED),
    ],
)
def test_gate_failures_block(tmp_path: Path, path_name: str, patch: dict[str, object], expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(getattr(settings, path_name), patch)

    result = run_metric_computation(settings)

    assert result.status == expected_status
    assert result.metric_result_rows_created is False
    _assert_downstream_flags_false(result)


@pytest.mark.parametrize(
    ("column", "expected_status"),
    [
        ("label_value", METRIC_COMPUTATION_SAMPLE_SCOPE_BLOCKED),
        ("split_role", METRIC_COMPUTATION_SAMPLE_SCOPE_BLOCKED),
        ("source_hash_coverage", METRIC_COMPUTATION_LINEAGE_BLOCKED),
        ("revision_id_coverage", METRIC_COMPUTATION_LINEAGE_BLOCKED),
        ("available_time_coverage", METRIC_COMPUTATION_LINEAGE_BLOCKED),
        ("quality_status_coverage", METRIC_COMPUTATION_LINEAGE_BLOCKED),
        ("forward_return_label_id", METRIC_COMPUTATION_LINEAGE_BLOCKED),
    ],
)
def test_missing_sample_row_required_fields_block(tmp_path: Path, column: str, expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    rows = pd.read_csv(settings.training_evaluation_sample_rows_path, dtype={"symbol": "string"})
    rows = rows.drop(columns=[column])
    rows.to_csv(settings.training_evaluation_sample_rows_path, index=False)

    result = run_metric_computation(settings)

    assert result.status == expected_status
    assert result.metrics_computed is False


def test_duplicate_sample_rows_without_quarantine_blocks(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    rows = pd.read_csv(settings.training_evaluation_sample_rows_path, dtype={"symbol": "string"})
    rows = pd.concat([rows, rows.iloc[[0]]], ignore_index=True)
    rows.to_csv(settings.training_evaluation_sample_rows_path, index=False)

    result = run_metric_computation(settings)

    assert result.status == METRIC_COMPUTATION_SAMPLE_SCOPE_BLOCKED


def test_non_numeric_label_values_are_quarantined(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    rows = _sample_rows()
    rows.append({**rows[0], "training_evaluation_sample_id": "sample_bad", "replay_decision_id": "decision_bad", "forward_return_label_id": "label_bad", "label_value": "bad"})
    _write_csv(settings.training_evaluation_sample_rows_path, rows)

    result = run_metric_computation(replace(settings, allow_metric_computation=True))

    assert result.status == METRIC_COMPUTATION_REPORT_CREATED
    assert result.sample_row_count == 4
    assert result.quarantined_sample_count == 1
    assert result.eligible_sample_count == 3


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_metric_computation(replace(_happy_settings(tmp_path), output_dir=tmp_path / "bad_outputs"))


def test_happy_path_without_allow_reaches_ready_and_creates_no_result_rows(tmp_path: Path) -> None:
    result = run_metric_computation(_happy_settings(tmp_path))

    assert result.status == READY_FOR_METRIC_COMPUTATION
    assert result.workflow_stage == READY_FOR_METRIC_COMPUTATION
    assert result.ready_for_metric_computation is True
    assert result.metric_computation_executed is False
    assert result.metric_computation_report_created is False
    assert result.metric_result_rows_created is False
    assert result.metric_summary_created is False
    assert result.metrics_computed is False
    assert result.sample_row_count == 3
    assert result.eligible_sample_count == 3
    assert pd.read_csv(result.artifact_paths["result_rows"]).empty
    _assert_downstream_flags_false(result)


def test_happy_path_with_allow_computes_only_allowed_report_only_metrics(tmp_path: Path) -> None:
    result = run_metric_computation(replace(_happy_settings(tmp_path), allow_metric_computation=True))

    assert result.status == METRIC_COMPUTATION_REPORT_CREATED
    assert result.workflow_stage == METRIC_COMPUTATION_REPORT_CREATED
    assert result.ready_for_metric_computation is True
    assert result.metric_computation_executed is True
    assert result.metric_computation_report_created is True
    assert result.metric_result_rows_created is True
    assert result.metric_summary_created is True
    assert result.metrics_computed is True
    assert result.unsupported_metrics_requested is False
    assert result.sample_row_count == 3
    assert result.eligible_sample_count == 3
    assert result.quarantined_sample_count == 0
    assert result.label_coverage_numerator == 3
    assert result.label_coverage_denominator == 3
    _assert_downstream_flags_false(result)

    rows = pd.read_csv(result.artifact_paths["result_rows"], dtype={"symbol": "string"})
    assert set(rows["metric_name"]) == set(ALLOWED_METRIC_SET)
    values = dict(zip(rows["metric_name"], rows["metric_value"]))
    assert values["sample_count"] == pytest.approx(3.0)
    assert values["label_coverage"] == pytest.approx(1.0)
    assert values["average_return"] == pytest.approx((0.10 - 0.05 + 0.20) / 3)
    assert values["median_return"] == pytest.approx(0.10)
    assert values["hit_rate"] == pytest.approx(2 / 3)
    assert rows["source_metric_evaluation_planning_run_id"].eq(result.source_metric_evaluation_planning_run_id).all()
    assert rows["source_training_evaluation_run_id"].eq("train_eval_metric_comp").all()
    assert rows["split_role"].eq("test").all()
    assert rows["label_name"].eq("forward_return_5d").all()
    assert rows["horizon_trading_days"].eq(5).all()
    assert rows["threshold_used"].fillna(0).eq(0).all()
    assert rows["report_only"].eq(True).all()
    assert rows["diagnostic_only"].eq(True).all()

    summary = pd.read_csv(result.artifact_paths["summary"])
    assert set(summary["metric_name"]) == set(ALLOWED_METRIC_SET)
    report = result.artifact_paths["report"].read_text(encoding="utf-8")
    for phrase in [
        "report-only historical metrics",
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
    for path in _output_text_paths(result):
        text = path.read_text(encoding="utf-8")
        assert "training_result artifact" not in text
        assert "model_weight" not in text
        assert "broker_order_id" not in text


def test_cli_no_input_runs(tmp_path: Path) -> None:
    completed = _run_cli(["metric-computation", "--output-dir", str(_output_dir(tmp_path))])

    assert "status: NO_METRIC_COMPUTATION_INPUT" in completed.stdout
    assert "metrics_computed: False" in completed.stdout
    assert "trading_allowed: False" in completed.stdout


def test_cli_happy_path_without_allow_reaches_ready(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    completed = _run_cli(_cli_args(settings))

    assert "status: READY_FOR_METRIC_COMPUTATION" in completed.stdout
    assert "metric_result_rows_created: False" in completed.stdout
    assert "metrics_computed: False" in completed.stdout


def test_cli_happy_path_with_allow_creates_report_only_result_rows(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    completed = _run_cli([*_cli_args(settings), "--allow-metric-computation"])

    assert "status: METRIC_COMPUTATION_REPORT_CREATED" in completed.stdout
    assert "metric_result_rows_created: True" in completed.stdout
    assert "metrics_computed: True" in completed.stdout
    assert "training_result_created: False" in completed.stdout


def test_only_metric_computation_cli_is_added_for_this_phase() -> None:
    help_text = _run_cli(["--help"]).stdout
    assert "metric-computation" in help_text
    assert "metric-computation-index" not in help_text
    assert "metric-computation-health" not in help_text
    assert "metric-computation-status" not in help_text


def test_no_research_status_checkpoint_or_project_source_integration_is_added() -> None:
    assert not Path("docs/release_checkpoint_v1.47.0.md").exists()
    assert not Path("docs/project_sources").exists()
    dashboard_text = Path("docs/local_research_dashboard.md").read_text(encoding="utf-8")
    assert "metric-computation-status" not in dashboard_text


def _happy_settings(tmp_path: Path) -> MetricComputationSettings:
    root = tmp_path / "fixtures"
    root.mkdir(parents=True, exist_ok=True)
    metric_eval = run_metric_evaluation(
        replace(
            _metric_evaluation_happy_settings(tmp_path),
            allow_metric_evaluation_planning_artifacts=True,
        )
    )
    training_dir = root / "training_evaluation_dataset"
    training_dir.mkdir(parents=True, exist_ok=True)
    training_metadata = _write_json(training_dir / "training_evaluation_metadata.json", _training_metadata(training_dir))
    sample_rows = _write_csv(training_dir / "training_evaluation_sample_rows.csv", _sample_rows())
    label_coverage = _write_csv(training_dir / "training_evaluation_label_coverage_report.csv", [{"label_name": "forward_return_5d", "row_count": 3}])
    safety_flags = _write_json(training_dir / "training_evaluation_safety_flags.json", _safe_flags())
    training_status = _write_csv(training_dir / "training_evaluation_status.csv", [{"status": "TRAINING_EVALUATION_DATASET_CREATED"}])
    training_health = _write_json(training_dir / "training_evaluation_health.json", {"status": "PASS"})

    return MetricComputationSettings(
        approval_manifest_path=_write_json(root / "approval.json", {"approval_text": EXACT_METRIC_COMPUTATION_APPROVAL_TEXT}),
        metric_computation_request_manifest_path=_write_json(root / "request.json", {"requested_metric_set": list(ALLOWED_METRIC_SET)}),
        metric_evaluation_metadata_path=metric_eval.artifact_paths["metadata"],
        metric_evaluation_input_index_path=metric_eval.artifact_paths["input_index"],
        metric_evaluation_metric_definitions_path=metric_eval.artifact_paths["metric_definitions"],
        metric_evaluation_sample_scope_path=metric_eval.artifact_paths["sample_scope"],
        metric_evaluation_denominator_rules_path=metric_eval.artifact_paths["denominator_rules"],
        metric_evaluation_safety_flags_path=metric_eval.artifact_paths["safety_flags"],
        metric_evaluation_status_artifact_path=metric_eval.artifact_paths["metadata"],
        metric_evaluation_health_artifact_path=_write_json(root / "metric_evaluation_health.json", {"status": "PASS"}),
        training_evaluation_metadata_path=training_metadata,
        training_evaluation_sample_rows_path=sample_rows,
        training_evaluation_label_coverage_report_path=label_coverage,
        training_evaluation_safety_flags_path=safety_flags,
        training_evaluation_status_artifact_path=training_status,
        training_evaluation_health_artifact_path=training_health,
        leakage_evidence_bundle_path=_write_json(root / "leakage.json", {"future_label_leakage": False}),
        overclaim_evidence_bundle_path=_write_json(root / "overclaim.json", _overclaim_flags()),
        side_effect_evidence_bundle_path=_write_json(root / "side_effect.json", _safe_flags()),
        output_dir=_output_dir(tmp_path),
    )


def _training_metadata(training_dir: Path) -> dict[str, object]:
    return {
        "training_evaluation_run_id": "train_eval_metric_comp",
        "status": "TRAINING_EVALUATION_DATASET_CREATED",
        "execution_status": "TRAINING_EVALUATION_DATASET_CREATED",
        "workflow_stage": "TRAINING_EVALUATION_DATASET_CREATED",
        "health_status": "PASS",
        "source_forward_return_label_run_id": "label_metric_comp",
        "source_replay_decision_freeze_run_id": "freeze_metric_comp",
        "training_evaluation_dataset_artifacts_created": True,
        "dataset_sample_row_count": 3,
        "label_row_count": 3,
        "symbol_count": 2,
        "label_name_set": "forward_return_5d",
        "artifact_path": str(training_dir),
        "report_only": True,
        "diagnostic_only": True,
    } | _safe_flags()


def _sample_rows() -> list[dict[str, object]]:
    base = {
        "training_evaluation_run_id": "train_eval_metric_comp",
        "replay_decision_freeze_run_id": "freeze_metric_comp",
        "forward_return_label_run_id": "label_metric_comp",
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
            "replay_decision_id": "decision_000001_20240402",
            "forward_return_label_id": "label_001",
            "symbol": "000001",
            "label_value": 0.10,
        },
        {
            **base,
            "training_evaluation_sample_id": "sample_002",
            "replay_decision_id": "decision_000002_20240402",
            "forward_return_label_id": "label_002",
            "symbol": "000002",
            "label_value": -0.05,
        },
        {
            **base,
            "training_evaluation_sample_id": "sample_003",
            "replay_decision_id": "decision_159915_20240402",
            "forward_return_label_id": "label_003",
            "symbol": "159915",
            "label_value": 0.20,
        },
    ]


def _safe_flags() -> dict[str, object]:
    return {field: False for field in _downstream_false_fields()} | {"report_only": True, "diagnostic_only": True}


def _overclaim_flags() -> dict[str, object]:
    return {
        "metric_computation_not_strategy_validation": True,
        "metric_computation_not_training_result": True,
        "metric_computation_not_weights": True,
        "metric_computation_not_model_version": True,
        "metric_computation_not_thresholds": True,
        "metric_computation_not_predictions": True,
        "metric_computation_not_probabilities": True,
        "metric_computation_not_feature_importance": True,
        "metric_computation_not_stock_profile": True,
        "metric_computation_not_buy_review": True,
        "metric_computation_not_paper_approval": True,
        "metric_computation_not_performance_validation": True,
        "metric_computation_not_trading": True,
    }


def _downstream_false_fields() -> list[str]:
    return [
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


def _required_artifact_keys() -> list[str]:
    return [
        "metadata",
        "report",
        "input_index",
        "metric_definitions_used",
        "sample_scope_used",
        "denominator_rules_used",
        "result_rows",
        "summary",
        "safety_flags",
        "precondition_results",
        "approval_results",
        "input_lineage_results",
        "dataset_input_results",
        "metric_definition_results",
        "denominator_results",
        "result_row_results",
        "leakage_guard_results",
        "side_effect_guard_results",
        "overclaim_guard_results",
        "recommended_next_task",
    ]


def _assert_downstream_flags_false(result) -> None:
    for field in _downstream_false_fields():
        assert getattr(result, field) is False, field


def _output_text_paths(result) -> list[Path]:
    return [path for path in result.artifact_paths.values() if path.suffix in {".csv", ".json", ".md"} and path.exists()]


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "metric_computation_v0_1"


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path | None, payload: dict[str, object]) -> Path:
    assert path is not None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _patch_json(path: Path | None, patch: dict[str, object]) -> None:
    assert path is not None
    payload = _read_json(path)
    payload.update(patch)
    _write_json(path, payload)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _cli_args(settings: MetricComputationSettings) -> list[str]:
    args = ["metric-computation"]
    for flag, value in [
        ("--approval-manifest-path", settings.approval_manifest_path),
        ("--metric-computation-request-manifest-path", settings.metric_computation_request_manifest_path),
        ("--metric-evaluation-metadata-path", settings.metric_evaluation_metadata_path),
        ("--metric-evaluation-input-index-path", settings.metric_evaluation_input_index_path),
        ("--metric-evaluation-metric-definitions-path", settings.metric_evaluation_metric_definitions_path),
        ("--metric-evaluation-sample-scope-path", settings.metric_evaluation_sample_scope_path),
        ("--metric-evaluation-denominator-rules-path", settings.metric_evaluation_denominator_rules_path),
        ("--metric-evaluation-safety-flags-path", settings.metric_evaluation_safety_flags_path),
        ("--metric-evaluation-status-artifact-path", settings.metric_evaluation_status_artifact_path),
        ("--metric-evaluation-health-artifact-path", settings.metric_evaluation_health_artifact_path),
        ("--training-evaluation-metadata-path", settings.training_evaluation_metadata_path),
        ("--training-evaluation-sample-rows-path", settings.training_evaluation_sample_rows_path),
        ("--training-evaluation-label-coverage-report-path", settings.training_evaluation_label_coverage_report_path),
        ("--training-evaluation-safety-flags-path", settings.training_evaluation_safety_flags_path),
        ("--training-evaluation-status-artifact-path", settings.training_evaluation_status_artifact_path),
        ("--training-evaluation-health-artifact-path", settings.training_evaluation_health_artifact_path),
        ("--leakage-evidence-bundle-path", settings.leakage_evidence_bundle_path),
        ("--overclaim-evidence-bundle-path", settings.overclaim_evidence_bundle_path),
        ("--side-effect-evidence-bundle-path", settings.side_effect_evidence_bundle_path),
        ("--output-dir", settings.output_dir),
    ]:
        if value is not None:
            args.extend([flag, str(value)])
    return args


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    return subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", *args],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
    )
