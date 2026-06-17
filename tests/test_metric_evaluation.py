from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.metric_evaluation import (
    EXACT_METRIC_EVALUATION_APPROVAL_TEXT,
    METRIC_EVALUATION_APPROVAL_BLOCKED,
    METRIC_EVALUATION_DATASET_HEALTH_BLOCKED,
    METRIC_EVALUATION_DATASET_INPUT_BLOCKED,
    METRIC_EVALUATION_LINEAGE_BLOCKED,
    METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED,
    METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED,
    NO_METRIC_EVALUATION_INPUT,
    READY_FOR_METRIC_EVALUATION_PLANNING_ARTIFACTS,
    MetricEvaluationSettings,
    run_metric_evaluation,
)
from quant_replay_system.metric_evaluation_health import check_metric_evaluation_health
from quant_replay_system.metric_evaluation_index import build_metric_evaluation_index
from quant_replay_system.metric_evaluation_status import run_metric_evaluation_status


def test_no_input_writes_required_artifacts_with_safe_defaults(tmp_path: Path) -> None:
    result = run_metric_evaluation(MetricEvaluationSettings(output_dir=_output_dir(tmp_path)))

    assert result.status == NO_METRIC_EVALUATION_INPUT
    assert result.workflow_stage == "METRIC_EVALUATION_NO_INPUT"
    assert result.ready_for_metric_evaluation_planning_artifacts is False
    assert result.metric_evaluation_executed is False
    assert result.metric_evaluation_planning_artifacts_created is False
    assert result.metric_evaluation_input_index_created is False
    assert result.metric_definitions_created is False
    assert result.sample_scope_created is False
    assert result.denominator_rules_created is False
    assert result.health_status_plan_created is False
    assert result.research_status_plan_created is False
    _assert_forbidden_flags_false(result)
    for key in _required_artifact_keys():
        assert result.artifact_paths[key].exists(), key
    metadata = _read_json(result.artifact_paths["metadata"])
    safety = _read_json(result.artifact_paths["safety_flags"])
    assert metadata["execution_status"] == NO_METRIC_EVALUATION_INPUT
    assert metadata["ready_for_metric_evaluation_planning_artifacts"] is False
    for field in _forbidden_false_fields():
        assert metadata[field] is False
        assert safety[field] is False


@pytest.mark.parametrize(
    "approval_text",
    [
        "",
        "continue",
        "go ahead",
        "do the next task",
        "compute metrics",
        "run evaluation",
        "train the model",
    ],
)
def test_vague_approval_blocks(tmp_path: Path, approval_text: str) -> None:
    settings = _happy_settings(tmp_path)
    _write_json(settings.approval_manifest_path, {"approval_text": approval_text})

    result = run_metric_evaluation(settings)

    assert result.status == METRIC_EVALUATION_APPROVAL_BLOCKED
    assert result.ready_for_metric_evaluation_planning_artifacts is False
    assert result.metric_evaluation_planning_artifacts_created is False
    _assert_forbidden_flags_false(result)


@pytest.mark.parametrize(
    "request_patch",
    [
        {"metric_computation_requested": True},
        {"metric_result_rows_requested": True},
        {"metric_evaluation_results_requested": True},
        {"evaluation_result_summary_requested": True},
        {"training_result_requested": True},
        {"weights_requested": True},
        {"model_version_requested": True},
        {"thresholds_requested": True},
        {"predictions_requested": True},
        {"calibrated_probabilities_requested": True},
        {"feature_importance_requested": True},
        {"stock_profile_requested": True},
        {"buy_review_requested": True},
        {"paper_approval_requested": True},
        {"performance_validation_requested": True},
        {"trading_requested": True},
    ],
)
def test_requests_outside_structural_planning_block(tmp_path: Path, request_patch: dict[str, object]) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.metric_evaluation_request_manifest_path, request_patch)

    result = run_metric_evaluation(settings)

    assert result.status in {
        "METRIC_EVALUATION_COMPUTATION_BLOCKED",
        "METRIC_EVALUATION_RESULT_ROWS_BLOCKED",
        "METRIC_EVALUATION_OVERCLAIM_BLOCKED",
        "METRIC_EVALUATION_SIDE_EFFECT_BLOCKED",
    }
    assert result.metric_evaluation_planning_artifacts_created is False
    _assert_forbidden_flags_false(result)


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("training_evaluation_metadata_path", METRIC_EVALUATION_DATASET_INPUT_BLOCKED),
        ("training_evaluation_dataset_index_path", METRIC_EVALUATION_DATASET_INPUT_BLOCKED),
        ("training_evaluation_sample_rows_path", METRIC_EVALUATION_DATASET_INPUT_BLOCKED),
        ("training_evaluation_label_coverage_report_path", METRIC_EVALUATION_DATASET_INPUT_BLOCKED),
        ("training_evaluation_split_plan_path", METRIC_EVALUATION_DATASET_INPUT_BLOCKED),
        ("training_evaluation_feature_plan_path", METRIC_EVALUATION_DATASET_INPUT_BLOCKED),
        ("training_evaluation_label_plan_path", METRIC_EVALUATION_DATASET_INPUT_BLOCKED),
        ("training_evaluation_safety_flags_path", METRIC_EVALUATION_DATASET_INPUT_BLOCKED),
        ("training_evaluation_status_artifact_path", METRIC_EVALUATION_DATASET_HEALTH_BLOCKED),
        ("training_evaluation_health_artifact_path", METRIC_EVALUATION_DATASET_HEALTH_BLOCKED),
        ("metric_definition_request_path", "METRIC_EVALUATION_DEFINITION_BLOCKED"),
        ("sample_scope_request_path", METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED),
        ("denominator_rule_request_path", METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED),
        ("benchmark_industry_request_path", METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED),
        ("leakage_evidence_bundle_path", "METRIC_EVALUATION_LEAKAGE_BLOCKED"),
        ("overclaim_evidence_bundle_path", "METRIC_EVALUATION_OVERCLAIM_BLOCKED"),
        ("side_effect_evidence_bundle_path", "METRIC_EVALUATION_SIDE_EFFECT_BLOCKED"),
    ],
)
def test_missing_required_inputs_block_by_gate(
    tmp_path: Path,
    setting_name: str,
    expected_status: str,
) -> None:
    result = run_metric_evaluation(replace(_happy_settings(tmp_path), **{setting_name: None}))

    assert result.status == expected_status
    assert result.metric_evaluation_planning_artifacts_created is False


@pytest.mark.parametrize(
    ("path_name", "patch", "expected_status"),
    [
        ("training_evaluation_metadata_path", {"status": "NO_TRAINING_EVALUATION_INPUT"}, METRIC_EVALUATION_DATASET_INPUT_BLOCKED),
        ("training_evaluation_metadata_path", {"training_evaluation_dataset_artifacts_created": False}, METRIC_EVALUATION_DATASET_INPUT_BLOCKED),
        ("training_evaluation_metadata_path", {"source_replay_decision_freeze_run_id": ""}, METRIC_EVALUATION_LINEAGE_BLOCKED),
        ("training_evaluation_metadata_path", {"source_forward_return_label_run_id": ""}, METRIC_EVALUATION_LINEAGE_BLOCKED),
        ("training_evaluation_health_artifact_path", {"status": "FAIL"}, METRIC_EVALUATION_DATASET_HEALTH_BLOCKED),
        ("training_evaluation_sample_rows_path", {"label_value": ""}, METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED),
        ("training_evaluation_sample_rows_path", {"split_role": ""}, METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED),
        ("training_evaluation_dataset_index_path", {"source_hash_coverage": "MISSING"}, METRIC_EVALUATION_LINEAGE_BLOCKED),
        ("sample_scope_request_path", {"valid_sample_scope": False}, METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED),
        ("denominator_rule_request_path", {"valid_denominator_rules": False}, METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED),
        ("benchmark_industry_request_path", {"valid_benchmark_industry_plan": False}, METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED),
        ("leakage_evidence_bundle_path", {"future_feature_leakage": True}, "METRIC_EVALUATION_LEAKAGE_BLOCKED"),
        ("side_effect_evidence_bundle_path", {"broker_api_called": True}, "METRIC_EVALUATION_SIDE_EFFECT_BLOCKED"),
        ("overclaim_evidence_bundle_path", {"metric_evaluation_not_performance_validation": False}, "METRIC_EVALUATION_OVERCLAIM_BLOCKED"),
    ],
)
def test_gate_failures_block(tmp_path: Path, path_name: str, patch: dict[str, object], expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(getattr(settings, path_name), patch)

    result = run_metric_evaluation(settings)

    assert result.status == expected_status
    assert result.metric_evaluation_planning_artifacts_created is False
    _assert_forbidden_flags_false(result)


def test_duplicate_sample_rows_without_quarantine_blocks(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    rows = pd.read_csv(settings.training_evaluation_sample_rows_path, dtype={"symbol": "string"})
    rows = pd.concat([rows, rows], ignore_index=True)
    rows.to_csv(settings.training_evaluation_sample_rows_path, index=False)
    _patch_json(settings.sample_scope_request_path, {"duplicate_sample_rows_quarantined": False})

    result = run_metric_evaluation(settings)

    assert result.status == METRIC_EVALUATION_SAMPLE_SCOPE_BLOCKED


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_metric_evaluation(replace(_happy_settings(tmp_path), output_dir=tmp_path / "bad_outputs"))


def test_happy_path_without_allow_reaches_ready_and_creates_no_planning_artifacts(tmp_path: Path) -> None:
    result = run_metric_evaluation(_happy_settings(tmp_path))

    assert result.status == READY_FOR_METRIC_EVALUATION_PLANNING_ARTIFACTS
    assert result.workflow_stage == READY_FOR_METRIC_EVALUATION_PLANNING_ARTIFACTS
    assert result.ready_for_metric_evaluation_planning_artifacts is True
    assert result.metric_evaluation_executed is False
    assert result.metric_evaluation_planning_artifacts_created is False
    assert result.metric_evaluation_input_index_created is False
    assert result.metric_definitions_created is False
    assert pd.read_csv(result.artifact_paths["input_index"]).empty
    _assert_forbidden_flags_false(result)


def test_happy_path_with_allow_creates_structural_planning_artifacts(tmp_path: Path) -> None:
    result = run_metric_evaluation(replace(_happy_settings(tmp_path), allow_metric_evaluation_planning_artifacts=True))

    assert result.status == METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED
    assert result.workflow_stage == METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED
    assert result.ready_for_metric_evaluation_planning_artifacts is True
    assert result.metric_evaluation_executed is True
    assert result.metric_evaluation_planning_artifacts_created is True
    assert result.metric_evaluation_input_index_created is True
    assert result.metric_definitions_created is True
    assert result.sample_scope_created is True
    assert result.denominator_rules_created is True
    assert result.health_status_plan_created is True
    assert result.research_status_plan_created is True
    _assert_forbidden_flags_false(result)

    definitions = pd.read_csv(result.artifact_paths["metric_definitions"])
    assert {"hit_rate", "average_return", "rank_information_coefficient"} <= set(definitions["metric_name"])
    assert definitions["computation_allowed_in_current_phase"].eq(False).all()
    assert definitions["result_rows_allowed_in_current_phase"].eq(False).all()
    assert definitions["requires_future_exact_approval"].eq(True).all()
    forbidden = _forbidden_output_columns()
    for path in _csv_artifact_paths(result):
        columns = set(pd.read_csv(path, nrows=0).columns)
        assert not (columns & forbidden), f"{path.name}: {columns & forbidden}"
    assert not (result.artifact_paths["artifact_dir"] / "metric_evaluation_result_rows.csv").exists()
    report = result.artifact_paths["report"].read_text(encoding="utf-8")
    for phrase in [
        "structural planning only",
        "not metrics computed",
        "not metric result rows",
        "not training_result",
        "not weights",
        "not model_version",
        "not thresholds",
        "not predictions",
        "not stock_profile",
        "not buy-review",
        "not paper approval",
        "not performance validation",
        "not trading",
    ]:
        assert phrase in report


def test_cli_no_input_and_happy_paths(tmp_path: Path) -> None:
    no_input = _run_cli(["metric-evaluation", "--output-dir", str(_output_dir(tmp_path))])
    assert "status: NO_METRIC_EVALUATION_INPUT" in no_input.stdout
    assert "metrics_computed: False" in no_input.stdout

    settings = _happy_settings(tmp_path)
    no_allow = _run_cli(_cli_args(settings, allow=False))
    allow = _run_cli(_cli_args(settings, allow=True))
    assert "status: READY_FOR_METRIC_EVALUATION_PLANNING_ARTIFACTS" in no_allow.stdout
    assert "metric_evaluation_planning_artifacts_created: False" in no_allow.stdout
    assert "status: METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED" in allow.stdout
    assert "metric_definitions_created: True" in allow.stdout
    assert "metric_result_rows_created: False" in allow.stdout
    assert "trading_allowed: False" in allow.stdout


def test_metric_evaluation_index_discovers_report_only_artifacts(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    no_input = run_metric_evaluation(MetricEvaluationSettings(output_dir=root))
    settings = _happy_settings(tmp_path)
    ready = run_metric_evaluation(settings)
    created = run_metric_evaluation(replace(settings, allow_metric_evaluation_planning_artifacts=True))

    index = build_metric_evaluation_index(root=root, output_dir=root / "index")

    assert index.artifact_count == 3
    assert set(index.index_frame["metric_evaluation_run_id"]) == {
        no_input.metric_evaluation_run_id,
        ready.metric_evaluation_run_id,
        created.metric_evaluation_run_id,
    }
    created_row = index.index_frame[index.index_frame["metric_evaluation_run_id"] == created.metric_evaluation_run_id].iloc[0]
    assert created_row["status"] == METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED
    assert created_row["metric_evaluation_planning_artifacts_created"] is True
    assert created_row["metric_definition_count"] == created.metric_definition_count
    assert created_row["sample_scope_row_count"] == created.sample_scope_row_count
    assert created_row["metrics_computed"] is False
    assert created_row["metric_result_rows_created"] is False
    assert created_row["training_result_created"] is False
    assert created_row["model_version_created"] is False
    assert created_row["stock_profile_created"] is False
    assert created_row["trading_allowed"] is False
    assert index.artifact_paths["index_csv"].exists()


def test_metric_evaluation_health_passes_for_valid_report_only_artifacts(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    run_metric_evaluation(MetricEvaluationSettings(output_dir=root))
    settings = _happy_settings(tmp_path)
    run_metric_evaluation(settings)
    run_metric_evaluation(replace(settings, allow_metric_evaluation_planning_artifacts=True))

    health = check_metric_evaluation_health(root=root, output_dir=root / "health")

    assert health.status == "PASS"
    assert health.error_count == 0
    assert health.warning_count == 0
    assert health.checked_artifact_count == 3
    assert health.artifact_paths["health_csv"].exists()


@pytest.mark.parametrize(
    ("patch", "expected_code"),
    [
        ({"approval_applied": True}, "APPROVAL_APPLIED_UNEXPECTED"),
        ({"metrics_computed": True}, "METRICS_COMPUTED_UNEXPECTED"),
        ({"metric_result_rows_created": True}, "METRIC_RESULT_ROWS_CREATED_UNEXPECTED"),
        ({"training_result_created": True}, "TRAINING_RESULT_CREATED_UNEXPECTED"),
        ({"model_version_created": True}, "MODEL_VERSION_CREATED_UNEXPECTED"),
        ({"stock_profile_created": True}, "STOCK_PROFILE_CREATED_UNEXPECTED"),
        ({"trading_allowed": True}, "TRADING_ALLOWED_UNEXPECTED"),
    ],
)
def test_metric_evaluation_health_fails_for_unsafe_metadata_flags(
    tmp_path: Path,
    patch: dict[str, object],
    expected_code: str,
) -> None:
    root = _output_dir(tmp_path)
    result = run_metric_evaluation(replace(_happy_settings(tmp_path), allow_metric_evaluation_planning_artifacts=True))
    _patch_json(result.artifact_paths["metadata"], patch)

    health = check_metric_evaluation_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert expected_code in set(health.health_frame["issue_code"])


def test_metric_evaluation_health_fails_if_created_artifact_is_missing(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    result = run_metric_evaluation(replace(_happy_settings(tmp_path), allow_metric_evaluation_planning_artifacts=True))
    result.artifact_paths["metric_definitions"].unlink()

    health = check_metric_evaluation_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "PLANNING_CREATED_WITHOUT_METRIC_DEFINITIONS" in set(health.health_frame["issue_code"])


def test_metric_evaluation_health_fails_for_result_rows_or_computed_columns(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    result = run_metric_evaluation(replace(_happy_settings(tmp_path), allow_metric_evaluation_planning_artifacts=True))
    pd.DataFrame([{"metric_name": "hit_rate", "metric_value": 0.5}]).to_csv(
        result.artifact_paths["artifact_dir"] / "metric_evaluation_result_rows.csv",
        index=False,
    )
    definitions = pd.read_csv(result.artifact_paths["metric_definitions"])
    definitions["computed_value"] = ""
    definitions.to_csv(result.artifact_paths["metric_definitions"], index=False)

    health = check_metric_evaluation_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "METRIC_RESULT_ROWS_ARTIFACT_UNEXPECTED" in set(health.health_frame["issue_code"])
    assert "CSV_FORBIDDEN_OUTPUT_COLUMNS" in set(health.health_frame["issue_code"])


def test_metric_evaluation_status_summarizes_latest_and_keeps_report_only_semantics(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    result = run_metric_evaluation(replace(_happy_settings(tmp_path), allow_metric_evaluation_planning_artifacts=True))

    status = run_metric_evaluation_status(root=root, output_dir=root / "status")

    assert status.latest_metric_evaluation_run_id == result.metric_evaluation_run_id
    assert status.status == METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED
    assert status.health_status == "PASS"
    assert status.workflow_stage == METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED
    assert status.metric_evaluation_planning_artifacts_created is True
    assert status.metrics_computed is False
    assert status.metric_result_rows_created is False
    assert status.training_allowed is False
    assert status.training_result_created is False
    assert status.model_version_created is False
    assert status.stock_profile_created is False
    assert status.trading_allowed is False
    assert "not metrics computed" in status.safety_statement
    assert "not trading" in status.safety_statement
    assert status.artifact_paths["status_csv"].exists()


def test_metric_evaluation_status_handles_no_artifacts(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)

    status = run_metric_evaluation_status(root=root, output_dir=root / "status")

    assert status.latest_metric_evaluation_run_id == ""
    assert status.health_status == "FAIL"
    assert status.workflow_stage == "NO_METRIC_EVALUATION_ARTIFACT_FOUND"
    assert status.metrics_computed is False
    assert status.metric_result_rows_created is False
    assert status.training_allowed is False
    assert status.trading_allowed is False


def test_metric_evaluation_artifact_view_cli_commands_work(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    run_metric_evaluation(replace(_happy_settings(tmp_path), allow_metric_evaluation_planning_artifacts=True))

    index = _run_cli(["metric-evaluation-index", "--root", str(root), "--output-dir", str(root / "index")])
    health = _run_cli(["metric-evaluation-health", "--root", str(root), "--output-dir", str(root / "health")])
    status = _run_cli(["metric-evaluation-status", "--root", str(root), "--output-dir", str(root / "status")])

    assert "artifact_count: 1" in index.stdout
    assert "status: PASS" in health.stdout
    assert "workflow_stage: METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED" in status.stdout
    assert "metrics_computed: False" in status.stdout
    assert "trading_allowed: False" in status.stdout


def test_artifact_views_exist_with_research_status_checkpoint_but_without_project_source() -> None:
    assert _command_exists("metric-evaluation-index")
    assert _command_exists("metric-evaluation-health")
    assert _command_exists("metric-evaluation-status")
    checkpoint = Path("docs/release_checkpoint_v1.46.0.md")
    assert checkpoint.exists()
    checkpoint_text = checkpoint.read_text(encoding="utf-8").lower()
    assert "research-status" in checkpoint_text
    assert "does not compute metrics" in checkpoint_text
    assert "does not create metric/evaluation result rows" in checkpoint_text
    assert "does not authorize trading" in checkpoint_text
    assert not Path("docs/project_sources").exists()


def _happy_settings(tmp_path: Path) -> MetricEvaluationSettings:
    root = tmp_path / "fixtures"
    root.mkdir(parents=True, exist_ok=True)
    source_run = root / "training_eval_source"
    source_run.mkdir()
    metadata = _write_json(source_run / "training_evaluation_metadata.json", _training_metadata(source_run))
    dataset_index = _write_csv(source_run / "training_evaluation_dataset_index.csv", _dataset_index_rows(source_run))
    sample_rows = _write_csv(source_run / "training_evaluation_sample_rows.csv", [_sample_row()])
    label_coverage = _write_csv(source_run / "training_evaluation_label_coverage_report.csv", [{"label_name": "forward_return_5d", "row_count": 1}])
    split_plan = _write_csv(source_run / "training_evaluation_split_plan.csv", [{"split_role": "test", "report_only": True}])
    feature_plan = _write_csv(source_run / "training_evaluation_feature_plan.csv", [{"plan_type": "feature_plan", "report_only": True}])
    label_plan = _write_csv(source_run / "training_evaluation_label_plan.csv", [{"label_name": "forward_return_5d", "report_only": True}])
    safety_flags = _write_json(source_run / "training_evaluation_safety_flags.json", _safe_flags())
    status_artifact = _write_csv(source_run / "training_evaluation_status.csv", [{"status": "TRAINING_EVALUATION_DATASET_CREATED"}])
    health_artifact = _write_csv(source_run / "training_evaluation_health.csv", [{"status": "PASS"}])

    return MetricEvaluationSettings(
        approval_manifest_path=_write_json(root / "approval.json", {"approval_text": EXACT_METRIC_EVALUATION_APPROVAL_TEXT}),
        metric_evaluation_request_manifest_path=_write_json(root / "request.json", {"metric_evaluation_phase_1_requested": True}),
        training_evaluation_metadata_path=metadata,
        training_evaluation_dataset_index_path=dataset_index,
        training_evaluation_sample_rows_path=sample_rows,
        training_evaluation_label_coverage_report_path=label_coverage,
        training_evaluation_split_plan_path=split_plan,
        training_evaluation_feature_plan_path=feature_plan,
        training_evaluation_label_plan_path=label_plan,
        training_evaluation_safety_flags_path=safety_flags,
        training_evaluation_status_artifact_path=status_artifact,
        training_evaluation_health_artifact_path=health_artifact,
        metric_definition_request_path=_write_json(root / "metric_definitions.json", {"valid_metric_definitions": True}),
        sample_scope_request_path=_write_json(root / "sample_scope.json", {"valid_sample_scope": True, "duplicate_sample_rows_quarantined": True}),
        denominator_rule_request_path=_write_json(root / "denominator_rules.json", {"valid_denominator_rules": True}),
        benchmark_industry_request_path=_write_json(root / "benchmark_industry.json", {"valid_benchmark_industry_plan": True}),
        leakage_evidence_bundle_path=_write_json(root / "leakage.json", {"future_feature_leakage": False}),
        overclaim_evidence_bundle_path=_write_json(root / "overclaim.json", _overclaim_flags()),
        side_effect_evidence_bundle_path=_write_json(root / "side_effect.json", _safe_flags()),
        output_dir=_output_dir(tmp_path),
    )


def _training_metadata(source_run: Path) -> dict[str, object]:
    return {
        "training_evaluation_run_id": "train_eval_abc123",
        "status": "TRAINING_EVALUATION_DATASET_CREATED",
        "execution_status": "TRAINING_EVALUATION_DATASET_CREATED",
        "workflow_stage": "TRAINING_EVALUATION_DATASET_CREATED",
        "health_status": "PASS",
        "source_forward_return_label_run_id": "label_abc123",
        "source_replay_decision_freeze_run_id": "freeze_abc123",
        "training_evaluation_dataset_artifacts_created": True,
        "dataset_sample_row_count": 1,
        "label_row_count": 1,
        "symbol_count": 1,
        "label_name_set": "forward_return_5d",
        "artifact_path": str(source_run),
        "report_only": True,
        "diagnostic_only": True,
    } | _safe_flags()


def _dataset_index_rows(source_run: Path) -> list[dict[str, object]]:
    return [
        {
            "artifact_name": "training_evaluation_sample_rows",
            "artifact_path": str(source_run / "training_evaluation_sample_rows.csv"),
            "source_hash_coverage": "PASS",
            "revision_id_coverage": "PASS",
            "available_time_coverage": "PASS",
            "quality_status_coverage": "PASS",
            "report_only": True,
            "diagnostic_only": True,
        }
    ]


def _sample_row() -> dict[str, object]:
    return {
        "training_evaluation_row_id": "row_001",
        "replay_decision_id": "decision_000001_20240402",
        "replay_decision_freeze_run_id": "freeze_abc123",
        "forward_return_label_run_id": "label_abc123",
        "symbol": "000001",
        "instrument_type": "STOCK",
        "replay_as_of_date": "2024-04-02",
        "feature_snapshot_ref": "features_20240402",
        "label_name": "forward_return_5d",
        "label_horizon_trading_days": 5,
        "label_start_date": "2024-04-02",
        "label_end_date": "2024-04-09",
        "label_value": 0.1,
        "label_source_field": "forward_return",
        "split_role": "test",
        "report_only": True,
        "diagnostic_only": True,
    }


def _safe_flags() -> dict[str, object]:
    return {field: False for field in _forbidden_false_fields()} | {"report_only": True, "diagnostic_only": True}


def _overclaim_flags() -> dict[str, object]:
    return {
        "metric_evaluation_not_metrics_computed": True,
        "metric_evaluation_not_result_rows": True,
        "metric_evaluation_not_training_result": True,
        "metric_evaluation_not_model_weights": True,
        "metric_evaluation_not_model_version": True,
        "metric_evaluation_not_stock_profile": True,
        "metric_evaluation_not_buy_review": True,
        "metric_evaluation_not_paper_approval": True,
        "metric_evaluation_not_performance_validation": True,
        "metric_evaluation_not_trading": True,
    }


def _forbidden_false_fields() -> list[str]:
    return [
        "metrics_computed",
        "metric_result_rows_created",
        "metric_evaluation_results_created",
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
        "metric_definitions",
        "sample_scope",
        "denominator_rules",
        "split_window_plan",
        "benchmark_industry_plan",
        "health_status_plan",
        "research_status_plan",
        "safety_flags",
        "precondition_results",
        "approval_results",
        "input_lineage_results",
        "dataset_scope_results",
        "metric_definition_results",
        "computation_exclusion_results",
        "leakage_guard_results",
        "side_effect_guard_results",
        "overclaim_guard_results",
        "recommended_next_task",
    ]


def _forbidden_output_columns() -> set[str]:
    return {
        "computed_value",
        "metric_value",
        "hit_rate_value",
        "average_return_value",
        "median_return_value",
        "benchmark_relative_performance",
        "industry_relative_performance",
        "ic_value",
        "sharpe_value",
        "profit_loss_ratio_value",
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


def _csv_artifact_paths(result: object) -> list[Path]:
    return [path for path in result.artifact_paths.values() if str(path).endswith(".csv")]


def _assert_forbidden_flags_false(result: object) -> None:
    for field in _forbidden_false_fields():
        assert getattr(result, field) is False, field


def _command_exists(command_name: str) -> bool:
    completed = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    return command_name in completed.stdout


def _cli_args(settings: MetricEvaluationSettings, *, allow: bool) -> list[str]:
    args = [
        "metric-evaluation",
        "--approval-manifest-path",
        str(settings.approval_manifest_path),
        "--metric-evaluation-request-manifest-path",
        str(settings.metric_evaluation_request_manifest_path),
        "--training-evaluation-metadata-path",
        str(settings.training_evaluation_metadata_path),
        "--training-evaluation-dataset-index-path",
        str(settings.training_evaluation_dataset_index_path),
        "--training-evaluation-sample-rows-path",
        str(settings.training_evaluation_sample_rows_path),
        "--training-evaluation-label-coverage-report-path",
        str(settings.training_evaluation_label_coverage_report_path),
        "--training-evaluation-split-plan-path",
        str(settings.training_evaluation_split_plan_path),
        "--training-evaluation-feature-plan-path",
        str(settings.training_evaluation_feature_plan_path),
        "--training-evaluation-label-plan-path",
        str(settings.training_evaluation_label_plan_path),
        "--training-evaluation-safety-flags-path",
        str(settings.training_evaluation_safety_flags_path),
        "--training-evaluation-status-artifact-path",
        str(settings.training_evaluation_status_artifact_path),
        "--training-evaluation-health-artifact-path",
        str(settings.training_evaluation_health_artifact_path),
        "--metric-definition-request-path",
        str(settings.metric_definition_request_path),
        "--sample-scope-request-path",
        str(settings.sample_scope_request_path),
        "--denominator-rule-request-path",
        str(settings.denominator_rule_request_path),
        "--benchmark-industry-request-path",
        str(settings.benchmark_industry_request_path),
        "--leakage-evidence-bundle-path",
        str(settings.leakage_evidence_bundle_path),
        "--overclaim-evidence-bundle-path",
        str(settings.overclaim_evidence_bundle_path),
        "--side-effect-evidence-bundle-path",
        str(settings.side_effect_evidence_bundle_path),
        "--output-dir",
        str(settings.output_dir),
    ]
    if allow:
        args.append("--allow-metric-evaluation-planning-artifacts")
    return args


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", *args],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
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
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path, dtype={"symbol": "string"})
        for key, value in patch.items():
            frame.loc[:, key] = value
        frame.to_csv(path, index=False)
    else:
        payload = _read_json(path)
        payload.update(patch)
        _write_json(path, payload)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "metric_evaluation_v0_1"
