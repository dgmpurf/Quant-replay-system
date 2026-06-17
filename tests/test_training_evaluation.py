from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.training_evaluation import (
    EXACT_APPROVAL_TEXT,
    NO_TRAINING_EVALUATION_INPUT,
    READY_FOR_TRAINING_EVALUATION_DATASET,
    TRAINING_EVALUATION_APPROVAL_BLOCKED,
    TRAINING_EVALUATION_DATASET_BOUNDARY_BLOCKED,
    TRAINING_EVALUATION_DATASET_CREATED,
    TRAINING_EVALUATION_FEATURE_GOVERNANCE_BLOCKED,
    TRAINING_EVALUATION_FORWARD_LABEL_BLOCKED,
    TRAINING_EVALUATION_FROZEN_DECISION_BLOCKED,
    TRAINING_EVALUATION_LABEL_PLAN_BLOCKED,
    TRAINING_EVALUATION_LEAKAGE_BLOCKED,
    TRAINING_EVALUATION_METRIC_BLOCKED,
    TRAINING_EVALUATION_OVERCLAIM_BLOCKED,
    TRAINING_EVALUATION_SIDE_EFFECT_BLOCKED,
    TRAINING_EVALUATION_SPLIT_BLOCKED,
    TrainingEvaluationSettings,
    run_training_evaluation,
)
from quant_replay_system.training_evaluation_health import check_training_evaluation_health
from quant_replay_system.training_evaluation_index import build_training_evaluation_index
from quant_replay_system.training_evaluation_status import run_training_evaluation_status


def test_no_input_writes_required_artifacts_with_safe_defaults(tmp_path: Path) -> None:
    result = run_training_evaluation(TrainingEvaluationSettings(output_dir=_output_dir(tmp_path)))

    assert result.status == NO_TRAINING_EVALUATION_INPUT
    assert result.workflow_stage == "TRAINING_EVALUATION_NO_INPUT"
    assert result.ready_for_training_evaluation_dataset is False
    assert result.training_evaluation_executed is False
    assert result.training_evaluation_dataset_artifacts_created is False
    assert result.bounded_sample_rows_created is False
    assert result.label_coverage_report_created is False
    assert result.split_plan_created is False
    assert result.feature_plan_created is False
    assert result.label_plan_created is False
    _assert_all_forbidden_flags_false(result)
    for key in _required_artifact_keys():
        assert result.artifact_paths[key].exists(), key
    metadata = _read_json(result.artifact_paths["metadata"])
    safety = _read_json(result.artifact_paths["safety_flags"])
    assert metadata["execution_status"] == NO_TRAINING_EVALUATION_INPUT
    assert metadata["ready_for_training_evaluation_dataset"] is False
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
        "start training",
        "compute metrics",
        "train the model",
        "create training_result",
        "optimize thresholds",
        "create stock_profile",
        "make buy candidates",
        "paper approve it",
        "validate performance",
        "trade it",
        "I authorize report-only training/evaluation and metrics.",
        "I authorize report-only training/evaluation and training_result.",
        "I authorize report-only training/evaluation and weights.",
        "I authorize report-only training/evaluation and model_version.",
        "I authorize report-only training/evaluation and thresholds.",
        "I authorize report-only training/evaluation and stock_profile.",
        "I authorize report-only training/evaluation and buy-review.",
        "I authorize report-only training/evaluation and paper approval.",
        "I authorize report-only training/evaluation and performance validation.",
        "I authorize report-only training/evaluation and trading.",
    ],
)
def test_approval_wording_must_be_exact_and_narrow(tmp_path: Path, approval_text: str) -> None:
    settings = _happy_settings(tmp_path)
    _write_json(settings.approval_manifest_path, {"approval_text": approval_text})

    result = run_training_evaluation(settings)

    assert result.status == TRAINING_EVALUATION_APPROVAL_BLOCKED
    assert result.ready_for_training_evaluation_dataset is False
    assert result.training_evaluation_dataset_artifacts_created is False
    _assert_all_forbidden_flags_false(result)


@pytest.mark.parametrize(
    ("patch", "expected_status"),
    [
        ({"status": "NO_FORWARD_RETURN_LABEL_INPUT"}, TRAINING_EVALUATION_FORWARD_LABEL_BLOCKED),
        ({"health_status": "FAIL"}, TRAINING_EVALUATION_FORWARD_LABEL_BLOCKED),
        ({"forward_labels_exist": False}, TRAINING_EVALUATION_FORWARD_LABEL_BLOCKED),
        ({"forward_return_labels_created": False}, TRAINING_EVALUATION_FORWARD_LABEL_BLOCKED),
    ],
)
def test_forward_label_metadata_or_health_blocks(tmp_path: Path, patch: dict[str, object], expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.forward_return_label_metadata_path, patch)

    result = run_training_evaluation(settings)

    assert result.status == expected_status
    assert result.training_evaluation_dataset_artifacts_created is False


@pytest.mark.parametrize(
    "missing_column",
    [
        "replay_decision_id",
        "replay_decision_freeze_run_id",
        "forward_return_label_run_id",
        "price_source_hash",
        "price_revision_id",
        "price_available_time",
        "price_quality_status",
    ],
)
def test_forward_label_rows_missing_lineage_or_price_fields_block(tmp_path: Path, missing_column: str) -> None:
    settings = _happy_settings(tmp_path)
    frame = pd.read_csv(settings.forward_return_label_rows_path, dtype={"symbol": "string"})
    frame = frame.drop(columns=[missing_column])
    frame.to_csv(settings.forward_return_label_rows_path, index=False)

    result = run_training_evaluation(settings)

    assert result.status == TRAINING_EVALUATION_FORWARD_LABEL_BLOCKED


def test_missing_forward_label_rows_block_when_dataset_creation_requested(tmp_path: Path) -> None:
    settings = replace(_happy_settings(tmp_path), allow_training_evaluation_dataset=True)
    settings.forward_return_label_rows_path.unlink()

    result = run_training_evaluation(settings)

    assert result.status == TRAINING_EVALUATION_FORWARD_LABEL_BLOCKED
    assert result.training_evaluation_dataset_artifacts_created is False


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("replay_decision_metadata_path", TRAINING_EVALUATION_FROZEN_DECISION_BLOCKED),
        ("replay_decision_rows_path", TRAINING_EVALUATION_FROZEN_DECISION_BLOCKED),
        ("replay_decision_evidence_index_path", TRAINING_EVALUATION_FROZEN_DECISION_BLOCKED),
        ("factor_observation_index_path", TRAINING_EVALUATION_FEATURE_GOVERNANCE_BLOCKED),
        ("event_structured_index_path", TRAINING_EVALUATION_FEATURE_GOVERNANCE_BLOCKED),
        ("company_exposure_index_path", TRAINING_EVALUATION_FEATURE_GOVERNANCE_BLOCKED),
        ("source_registry_path", TRAINING_EVALUATION_FEATURE_GOVERNANCE_BLOCKED),
        ("split_plan_request_path", TRAINING_EVALUATION_SPLIT_BLOCKED),
        ("feature_plan_request_path", TRAINING_EVALUATION_FEATURE_GOVERNANCE_BLOCKED),
        ("label_plan_request_path", TRAINING_EVALUATION_LABEL_PLAN_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", TRAINING_EVALUATION_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", TRAINING_EVALUATION_OVERCLAIM_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(
    tmp_path: Path,
    setting_name: str,
    expected_status: str,
) -> None:
    result = run_training_evaluation(replace(_happy_settings(tmp_path), **{setting_name: None}))

    assert result.status == expected_status
    assert result.training_evaluation_dataset_artifacts_created is False


@pytest.mark.parametrize(
    ("path_name", "patch", "expected_status"),
    [
        ("replay_decision_metadata_path", {"execution_status": "READY_FOR_REPLAY_DECISION_FREEZE"}, TRAINING_EVALUATION_FROZEN_DECISION_BLOCKED),
        ("replay_decision_metadata_path", {"replay_decision_frozen": False}, TRAINING_EVALUATION_FROZEN_DECISION_BLOCKED),
        ("factor_observation_index_path", {"available_time_coverage": "missing"}, TRAINING_EVALUATION_FEATURE_GOVERNANCE_BLOCKED),
        ("feature_plan_request_path", {"uses_future_label_as_feature": True}, TRAINING_EVALUATION_FEATURE_GOVERNANCE_BLOCKED),
        ("feature_plan_request_path", {"uses_future_price_as_feature": True}, TRAINING_EVALUATION_FEATURE_GOVERNANCE_BLOCKED),
        ("feature_plan_request_path", {"uses_paper_outcome_as_feature": True}, TRAINING_EVALUATION_FEATURE_GOVERNANCE_BLOCKED),
        ("feature_plan_request_path", {"uses_stock_profile_fields": True}, TRAINING_EVALUATION_FEATURE_GOVERNANCE_BLOCKED),
        ("feature_plan_request_path", {"uses_broker_order_fill_fields": True}, TRAINING_EVALUATION_FEATURE_GOVERNANCE_BLOCKED),
        ("split_plan_request_path", {"valid_split_plan": False}, TRAINING_EVALUATION_SPLIT_BLOCKED),
        ("label_plan_request_path", {"forward_labels_target_only": False}, TRAINING_EVALUATION_LABEL_PLAN_BLOCKED),
        ("training_evaluation_request_manifest_path", {"metrics_computation_requested": True}, TRAINING_EVALUATION_METRIC_BLOCKED),
        ("training_evaluation_request_manifest_path", {"training_result_requested": True}, TRAINING_EVALUATION_METRIC_BLOCKED),
        ("training_evaluation_request_manifest_path", {"weights_requested": True}, TRAINING_EVALUATION_METRIC_BLOCKED),
        ("training_evaluation_request_manifest_path", {"model_version_requested": True}, TRAINING_EVALUATION_METRIC_BLOCKED),
        ("training_evaluation_request_manifest_path", {"thresholds_requested": True}, TRAINING_EVALUATION_METRIC_BLOCKED),
        ("training_evaluation_request_manifest_path", {"predictions_requested": True}, TRAINING_EVALUATION_METRIC_BLOCKED),
        ("training_evaluation_request_manifest_path", {"calibrated_probabilities_requested": True}, TRAINING_EVALUATION_METRIC_BLOCKED),
        ("training_evaluation_request_manifest_path", {"feature_importance_requested": True}, TRAINING_EVALUATION_METRIC_BLOCKED),
        ("training_evaluation_request_manifest_path", {"stock_profile_requested": True}, TRAINING_EVALUATION_LEAKAGE_BLOCKED),
        ("training_evaluation_request_manifest_path", {"buy_review_requested": True}, TRAINING_EVALUATION_OVERCLAIM_BLOCKED),
        ("training_evaluation_request_manifest_path", {"paper_approval_requested": True}, TRAINING_EVALUATION_OVERCLAIM_BLOCKED),
        ("training_evaluation_request_manifest_path", {"performance_validation_requested": True}, TRAINING_EVALUATION_OVERCLAIM_BLOCKED),
        ("training_evaluation_request_manifest_path", {"trading_requested": True}, TRAINING_EVALUATION_SIDE_EFFECT_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", {"broker_api_called": True}, TRAINING_EVALUATION_SIDE_EFFECT_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", {"cache_mutated": True}, TRAINING_EVALUATION_SIDE_EFFECT_BLOCKED),
        ("overclaim_evidence_bundle_path", {"training_evaluation_not_performance_validation": False}, TRAINING_EVALUATION_OVERCLAIM_BLOCKED),
    ],
)
def test_gate_failures_block(tmp_path: Path, path_name: str, patch: dict[str, object], expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(getattr(settings, path_name), patch)

    result = run_training_evaluation(settings)

    assert result.status == expected_status
    assert result.training_evaluation_dataset_artifacts_created is False
    _assert_all_forbidden_flags_false(result)


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_training_evaluation(replace(_happy_settings(tmp_path), output_dir=tmp_path / "bad_outputs"))


def test_happy_path_without_allow_reaches_ready_and_creates_no_dataset(tmp_path: Path) -> None:
    result = run_training_evaluation(_happy_settings(tmp_path))

    assert result.status == READY_FOR_TRAINING_EVALUATION_DATASET
    assert result.workflow_stage == READY_FOR_TRAINING_EVALUATION_DATASET
    assert result.ready_for_training_evaluation_dataset is True
    assert result.training_evaluation_executed is False
    assert result.training_evaluation_dataset_artifacts_created is False
    assert result.bounded_sample_rows_created is False
    assert result.label_coverage_report_created is False
    assert pd.read_csv(result.artifact_paths["training_evaluation_sample_rows"]).empty
    _assert_all_forbidden_flags_false(result)


def test_happy_path_with_explicit_allow_creates_report_only_dataset_planning_artifacts(tmp_path: Path) -> None:
    result = run_training_evaluation(replace(_happy_settings(tmp_path), allow_training_evaluation_dataset=True))

    assert result.status == TRAINING_EVALUATION_DATASET_CREATED
    assert result.workflow_stage == TRAINING_EVALUATION_DATASET_CREATED
    assert result.ready_for_training_evaluation_dataset is True
    assert result.training_evaluation_executed is True
    assert result.training_evaluation_dataset_artifacts_created is True
    assert result.bounded_sample_rows_created is True
    assert result.label_coverage_report_created is True
    assert result.split_plan_created is True
    assert result.feature_plan_created is True
    assert result.label_plan_created is True
    _assert_all_forbidden_flags_false(result)

    sample = pd.read_csv(result.artifact_paths["training_evaluation_sample_rows"], dtype={"symbol": "string"})
    assert sample["symbol"].iloc[0] == "000001"
    assert sample["replay_decision_freeze_run_id"].iloc[0] == "freeze_abc123"
    assert sample["forward_return_label_run_id"].iloc[0] == "label_abc123"
    assert sample["label_source_field"].iloc[0] == "forward_return"
    forbidden_columns = _forbidden_output_columns()
    for path in _csv_artifact_paths(result):
        columns = set(pd.read_csv(path, nrows=0).columns)
        assert not (columns & forbidden_columns), f"{path.name}: {columns & forbidden_columns}"

    metadata = _read_json(result.artifact_paths["metadata"])
    assert metadata["training_evaluation_dataset_artifact_path"] == str(result.artifact_paths["training_evaluation_sample_rows"])
    assert metadata["metrics_computed"] is False
    assert metadata["training_result_created"] is False


def test_report_uses_required_safety_wording(tmp_path: Path) -> None:
    result = run_training_evaluation(replace(_happy_settings(tmp_path), allow_training_evaluation_dataset=True))
    report = result.artifact_paths["report"].read_text(encoding="utf-8")

    for phrase in [
        "dataset/planning-only",
        "not metrics",
        "not training_result",
        "not weights",
        "not model_version",
        "not stock_profile",
        "not buy-review",
        "not paper approval",
        "not performance validation",
        "not trading",
    ]:
        assert phrase in report


def test_cli_no_input_runs(tmp_path: Path) -> None:
    completed = _run_cli(["training-evaluation", "--output-dir", str(_output_dir(tmp_path))])

    assert "status: NO_TRAINING_EVALUATION_INPUT" in completed.stdout
    assert "ready_for_training_evaluation_dataset: False" in completed.stdout


def test_cli_happy_paths_with_and_without_allow(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    no_allow = _run_cli(_cli_args(settings, allow=False))
    allow = _run_cli(_cli_args(settings, allow=True))

    assert "status: READY_FOR_TRAINING_EVALUATION_DATASET" in no_allow.stdout
    assert "training_evaluation_dataset_artifacts_created: False" in no_allow.stdout
    assert "status: TRAINING_EVALUATION_DATASET_CREATED" in allow.stdout
    assert "training_evaluation_dataset_artifacts_created: True" in allow.stdout
    assert "metrics_computed: False" in allow.stdout


def test_no_artifact_views_research_status_checkpoint_or_project_source_are_added() -> None:
    assert not Path("docs/release_checkpoint_v1.45.0.md").exists()
    assert not Path("docs/project_sources").exists()


def test_training_evaluation_index_discovers_no_input_ready_and_created_artifacts(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    no_input = run_training_evaluation(TrainingEvaluationSettings(output_dir=root))
    ready = run_training_evaluation(_happy_settings(tmp_path))
    created = run_training_evaluation(replace(_happy_settings(tmp_path), allow_training_evaluation_dataset=True))

    index = build_training_evaluation_index(root=root, output_dir=root / "index")

    assert index.artifact_count == 3
    rows = index.index_frame.set_index("training_evaluation_run_id")
    assert rows.loc[no_input.training_evaluation_run_id, "status"] == NO_TRAINING_EVALUATION_INPUT
    assert rows.loc[ready.training_evaluation_run_id, "ready_for_training_evaluation_dataset"] is True
    assert rows.loc[created.training_evaluation_run_id, "training_evaluation_dataset_artifacts_created"] is True
    assert rows.loc[created.training_evaluation_run_id, "dataset_sample_row_count"] == 1
    assert rows.loc[created.training_evaluation_run_id, "symbol_count"] == 1
    assert rows.loc[created.training_evaluation_run_id, "label_name_set"] == "forward_return_5d"
    assert rows.loc[created.training_evaluation_run_id, "metrics_computed"] is False


@pytest.mark.parametrize(
    "settings_factory",
    [
        lambda tmp_path: TrainingEvaluationSettings(output_dir=_output_dir(tmp_path)),
        lambda tmp_path: _happy_settings(tmp_path),
        lambda tmp_path: replace(_happy_settings(tmp_path), allow_training_evaluation_dataset=True),
    ],
)
def test_training_evaluation_health_passes_valid_artifacts(tmp_path: Path, settings_factory: object) -> None:
    settings = settings_factory(tmp_path)
    run_training_evaluation(settings)

    health = check_training_evaluation_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "PASS"
    assert health.error_count == 0


@pytest.mark.parametrize(
    ("artifact_name", "expected_issue"),
    [
        ("training_evaluation_dataset_index.csv", "DATASET_CREATED_WITHOUT_DATASET_INDEX"),
        ("training_evaluation_sample_rows.csv", "DATASET_CREATED_WITHOUT_SAMPLE_ROWS"),
        ("training_evaluation_label_coverage_report.csv", "DATASET_CREATED_WITHOUT_LABEL_COVERAGE_REPORT"),
    ],
)
def test_training_evaluation_health_fails_when_created_artifacts_are_missing(
    tmp_path: Path,
    artifact_name: str,
    expected_issue: str,
) -> None:
    result = run_training_evaluation(replace(_happy_settings(tmp_path), allow_training_evaluation_dataset=True))
    (result.artifact_paths["artifact_dir"] / artifact_name).unlink()

    health = check_training_evaluation_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert expected_issue in set(health.health_frame["issue_code"])


@pytest.mark.parametrize(
    ("mutator", "expected_issue"),
    [
        ("drop_lineage", "SAMPLE_ROWS_REQUIRED_COLUMNS_MISSING"),
        ("drop_split_role", "SAMPLE_ROWS_REQUIRED_COLUMNS_MISSING"),
        ("metric_column", "SAMPLE_ROWS_FORBIDDEN_COLUMNS"),
        ("model_column", "SAMPLE_ROWS_FORBIDDEN_COLUMNS"),
        ("threshold_prediction_probability_importance_column", "SAMPLE_ROWS_FORBIDDEN_COLUMNS"),
        ("stock_profile_column", "SAMPLE_ROWS_FORBIDDEN_COLUMNS"),
        ("buy_review_column", "SAMPLE_ROWS_FORBIDDEN_COLUMNS"),
        ("paper_column", "SAMPLE_ROWS_FORBIDDEN_COLUMNS"),
        ("performance_column", "SAMPLE_ROWS_FORBIDDEN_COLUMNS"),
        ("trading_column", "SAMPLE_ROWS_FORBIDDEN_COLUMNS"),
    ],
)
def test_training_evaluation_health_fails_for_bad_sample_rows(
    tmp_path: Path,
    mutator: str,
    expected_issue: str,
) -> None:
    result = run_training_evaluation(replace(_happy_settings(tmp_path), allow_training_evaluation_dataset=True))
    _mutate_training_sample_rows(result.artifact_paths["artifact_dir"], mutator)

    health = check_training_evaluation_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert expected_issue in set(health.health_frame["issue_code"])


@pytest.mark.parametrize(
    "field",
    [
        "metrics_computed",
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
    ],
)
def test_training_evaluation_health_fails_for_unsafe_metadata_or_safety_flags(tmp_path: Path, field: str) -> None:
    result = run_training_evaluation(replace(_happy_settings(tmp_path), allow_training_evaluation_dataset=True))
    _patch_json(result.artifact_paths["metadata"], {field: True})

    health = check_training_evaluation_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert f"{field.upper()}_UNEXPECTED" in set(health.health_frame["issue_code"])


def test_training_evaluation_status_reports_no_input_ready_and_created_states(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    no_input = run_training_evaluation(TrainingEvaluationSettings(output_dir=root))
    no_input_status = run_training_evaluation_status(root=root, output_dir=root / "status_no_input")
    assert no_input_status.latest_training_evaluation_run_id == no_input.training_evaluation_run_id
    assert no_input_status.workflow_stage == "TRAINING_EVALUATION_NO_INPUT"

    ready = run_training_evaluation(_happy_settings(tmp_path))
    ready_status = run_training_evaluation_status(root=root, output_dir=root / "status_ready")
    assert ready_status.latest_training_evaluation_run_id == ready.training_evaluation_run_id
    assert ready_status.workflow_stage == READY_FOR_TRAINING_EVALUATION_DATASET
    assert ready_status.training_evaluation_dataset_artifacts_created is False

    created = run_training_evaluation(replace(_happy_settings(tmp_path), allow_training_evaluation_dataset=True))
    created_status = run_training_evaluation_status(root=root, output_dir=root / "status_created")
    assert created_status.latest_training_evaluation_run_id == created.training_evaluation_run_id
    assert created_status.workflow_stage == TRAINING_EVALUATION_DATASET_CREATED
    assert created_status.training_evaluation_dataset_artifacts_created is True
    assert created_status.metrics_computed is False
    for phrase in [
        "report-only dataset/planning-only",
        "does not compute metrics",
        "does not create training_result",
        "does not train weights",
        "does not create model_version",
        "does not optimize thresholds",
        "does not create predictions",
        "does not create stock_profile",
        "does not create buy-review eligibility",
        "does not apply paper approval",
        "does not claim strategy performance validation",
        "does not authorize trading",
    ]:
        assert phrase in created_status.safety_statement


def test_training_evaluation_cli_artifact_view_commands_run(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    run_training_evaluation(replace(_happy_settings(tmp_path), allow_training_evaluation_dataset=True))

    index = _run_cli(["training-evaluation-index", "--root", str(root), "--output-dir", str(root / "index")])
    health = _run_cli(["training-evaluation-health", "--root", str(root), "--output-dir", str(root / "health")])
    status = _run_cli(["training-evaluation-status", "--root", str(root), "--output-dir", str(root / "status")])

    assert "artifact_count: 1" in index.stdout
    assert "status: PASS" in health.stdout
    assert "workflow_stage: TRAINING_EVALUATION_DATASET_CREATED" in status.stdout
    assert "metrics_computed: False" in status.stdout


def test_training_evaluation_artifact_views_do_not_add_research_status_checkpoint_or_project_source() -> None:
    assert not Path("docs/release_checkpoint_v1.45.0.md").exists()
    assert not Path("docs/project_sources").exists()


def _happy_settings(tmp_path: Path) -> TrainingEvaluationSettings:
    root = tmp_path / "fixtures"
    root.mkdir(parents=True, exist_ok=True)
    approval = _write_json(root / "approval.json", {"approval_text": EXACT_APPROVAL_TEXT})
    request = _write_json(root / "request.json", {"training_evaluation_phase_1_requested": True})
    forward_metadata = _write_json(root / "forward_label_metadata.json", _forward_label_metadata())
    forward_rows = _write_forward_label_rows(root / "forward_label_rows.csv")
    forward_status = _write_csv(root / "forward_label_status.csv", [{"status": "FORWARD_RETURN_LABELS_CREATED"}])
    forward_health = _write_csv(root / "forward_label_health.csv", [{"status": "PASS"}])
    forward_safety = _write_json(root / "forward_label_safety.json", _safe_flags())
    replay_metadata = _write_json(root / "replay_decision_metadata.json", _replay_decision_metadata())
    replay_rows = _write_replay_decision_rows(root / "replay_decision_rows.csv")
    replay_evidence = _write_csv(
        root / "replay_decision_evidence.csv",
        [
            {
                "replay_decision_id": "decision_000001_20240402",
                "source_hash": "decision_hash",
                "revision_id": "decision_rev",
                "available_time": "2024-04-02T15:30:00+08:00",
                "quality_status": "PASS",
            }
        ],
    )
    factor = _write_csv(root / "factor.csv", [_coverage_row("factor_observation")])
    event = _write_csv(root / "event.csv", [_coverage_row("event_structured")])
    exposure = _write_csv(root / "exposure.csv", [_coverage_row("company_exposure")])
    source_registry = _write_csv(root / "source_registry.csv", [_coverage_row("source_registry")])
    split = _write_json(root / "split.json", {"valid_split_plan": True, "embargo_days": 5})
    feature = _write_json(root / "feature.json", {"valid_feature_plan": True})
    label = _write_json(root / "label.json", {"valid_label_plan": True, "forward_labels_target_only": True})
    leakage = _write_json(root / "leakage.json", _safe_flags())
    overclaim = _write_json(
        root / "overclaim.json",
        {
            "training_evaluation_not_training_result": True,
            "training_evaluation_not_model_weights": True,
            "training_evaluation_not_stock_profile": True,
            "training_evaluation_not_buy_review": True,
            "training_evaluation_not_paper_approval": True,
            "training_evaluation_not_performance_validation": True,
            "training_evaluation_not_trading": True,
            "strategy_performance_validated": False,
        },
    )
    return TrainingEvaluationSettings(
        approval_manifest_path=approval,
        training_evaluation_request_manifest_path=request,
        forward_return_label_metadata_path=forward_metadata,
        forward_return_label_rows_path=forward_rows,
        forward_return_label_status_artifact_path=forward_status,
        forward_return_label_health_artifact_path=forward_health,
        forward_return_label_safety_flags_path=forward_safety,
        replay_decision_metadata_path=replay_metadata,
        replay_decision_rows_path=replay_rows,
        replay_decision_evidence_index_path=replay_evidence,
        factor_observation_index_path=factor,
        event_structured_index_path=event,
        company_exposure_index_path=exposure,
        source_registry_path=source_registry,
        split_plan_request_path=split,
        feature_plan_request_path=feature,
        label_plan_request_path=label,
        leakage_side_effect_evidence_bundle_path=leakage,
        overclaim_evidence_bundle_path=overclaim,
        output_dir=_output_dir(tmp_path),
    )


def _forward_label_metadata() -> dict[str, object]:
    return {
        "forward_return_label_run_id": "label_abc123",
        "execution_status": "FORWARD_RETURN_LABELS_CREATED",
        "status": "FORWARD_RETURN_LABELS_CREATED",
        "workflow_stage": "FORWARD_RETURN_LABELS_CREATED",
        "health_status": "PASS",
        "source_replay_decision_freeze_run_id": "freeze_abc123",
        "forward_labels_exist": True,
        "forward_return_labels_created": True,
        "label_row_count": 1,
        "report_only": True,
        "diagnostic_only": True,
    } | _safe_flags()


def _replay_decision_metadata() -> dict[str, object]:
    return {
        "replay_decision_freeze_run_id": "freeze_abc123",
        "execution_status": "REPLAY_DECISION_FROZEN",
        "status": "REPLAY_DECISION_FROZEN",
        "workflow_stage": "REPLAY_DECISION_FROZEN",
        "health_status": "PASS",
        "replay_decision_frozen": True,
        "replay_decisions_exist": True,
        "decision_row_count": 1,
        "report_only": True,
        "diagnostic_only": True,
    } | _safe_flags()


def _write_forward_label_rows(path: Path) -> Path:
    return _write_csv(
        path,
        [
            {
                "forward_return_label_run_id": "label_abc123",
                "replay_decision_id": "decision_000001_20240402",
                "replay_decision_freeze_run_id": "freeze_abc123",
                "actual_replay_execution_run_id": "actual_001",
                "source_active_input_creation_run_id": "active_001",
                "source_real_replay_precheck_run_id": "precheck_001",
                "symbol": "000001",
                "instrument_type": "STOCK",
                "replay_as_of_date": "2024-04-02",
                "label_name": "forward_return_5d",
                "label_horizon_trading_days": 5,
                "label_start_date": "2024-04-02",
                "label_end_date": "2024-04-09",
                "forward_return": 0.1,
                "price_source_id": "price_source",
                "price_source_hash": "price_hash",
                "price_revision_id": "price_rev",
                "price_available_time": "2024-04-09T15:30:00+08:00",
                "price_quality_status": "PASS",
                "report_only": True,
                "diagnostic_only": True,
            }
        ],
    )


def _write_replay_decision_rows(path: Path) -> Path:
    return _write_csv(
        path,
        [
            {
                "replay_decision_id": "decision_000001_20240402",
                "replay_decision_freeze_run_id": "freeze_abc123",
                "replay_as_of_date": "2024-04-02",
                "symbol": "000001",
                "instrument_type": "STOCK",
                "decision_label": "WATCH",
                "feature_snapshot_ref": "features_20240402",
                "feature_available_time_max": "2024-04-02T15:30:00+08:00",
                "feature_source_hash_coverage": "PASS",
                "feature_revision_id_coverage": "PASS",
                "feature_quality_status": "PASS",
                "report_only": True,
                "diagnostic_only": True,
            }
        ],
    )


def _coverage_row(name: str) -> dict[str, object]:
    return {
        "artifact_name": name,
        "source_hash_coverage": "PASS",
        "revision_id_coverage": "PASS",
        "available_time_coverage": "PASS",
        "quality_status_coverage": "PASS",
        "report_only": True,
        "diagnostic_only": True,
    }


def _safe_flags() -> dict[str, object]:
    return {field: False for field in _forbidden_false_fields()} | {
        "report_only": True,
        "diagnostic_only": True,
    }


def _forbidden_false_fields() -> list[str]:
    return [
        "metrics_computed",
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
        "dataset_index",
        "sample_rows",
        "label_coverage_report",
        "split_plan",
        "feature_plan",
        "label_plan",
        "safety_flags",
        "precondition_results",
        "approval_results",
        "lineage_results",
        "dataset_boundary_results",
        "feature_governance_results",
        "split_guard_results",
        "label_guard_results",
        "leakage_side_effect_guard_results",
        "overclaim_guard_results",
        "recommended_next_task",
    ]


def _forbidden_output_columns() -> set[str]:
    return {
        "hit_rate",
        "average_return",
        "median_return",
        "benchmark_relative_performance",
        "industry_relative_performance",
        "ic",
        "sharpe",
        "profit_loss_ratio",
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
    paths = result.artifact_paths
    return [path for key, path in paths.items() if str(path).endswith(".csv")]


def _assert_all_forbidden_flags_false(result: object) -> None:
    for field in _forbidden_false_fields():
        assert getattr(result, field) is False, field


def _cli_args(settings: TrainingEvaluationSettings, *, allow: bool) -> list[str]:
    args = [
        "training-evaluation",
        "--approval-manifest-path",
        str(settings.approval_manifest_path),
        "--training-evaluation-request-manifest-path",
        str(settings.training_evaluation_request_manifest_path),
        "--forward-return-label-metadata-path",
        str(settings.forward_return_label_metadata_path),
        "--forward-return-label-rows-path",
        str(settings.forward_return_label_rows_path),
        "--forward-return-label-status-artifact-path",
        str(settings.forward_return_label_status_artifact_path),
        "--forward-return-label-health-artifact-path",
        str(settings.forward_return_label_health_artifact_path),
        "--forward-return-label-safety-flags-path",
        str(settings.forward_return_label_safety_flags_path),
        "--replay-decision-metadata-path",
        str(settings.replay_decision_metadata_path),
        "--replay-decision-rows-path",
        str(settings.replay_decision_rows_path),
        "--replay-decision-evidence-index-path",
        str(settings.replay_decision_evidence_index_path),
        "--factor-observation-index-path",
        str(settings.factor_observation_index_path),
        "--event-structured-index-path",
        str(settings.event_structured_index_path),
        "--company-exposure-index-path",
        str(settings.company_exposure_index_path),
        "--source-registry-path",
        str(settings.source_registry_path),
        "--split-plan-request-path",
        str(settings.split_plan_request_path),
        "--feature-plan-request-path",
        str(settings.feature_plan_request_path),
        "--label-plan-request-path",
        str(settings.label_plan_request_path),
        "--leakage-side-effect-evidence-bundle-path",
        str(settings.leakage_side_effect_evidence_bundle_path),
        "--overclaim-evidence-bundle-path",
        str(settings.overclaim_evidence_bundle_path),
        "--output-dir",
        str(settings.output_dir),
    ]
    if allow:
        args.append("--allow-training-evaluation-dataset")
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


def _mutate_training_sample_rows(artifact_dir: Path, mutator: str) -> None:
    rows_path = artifact_dir / "training_evaluation_sample_rows.csv"
    rows = pd.read_csv(rows_path, dtype={"symbol": "string"})
    if mutator == "drop_lineage":
        rows = rows.drop(columns=["replay_decision_freeze_run_id"])
    elif mutator == "drop_split_role":
        rows = rows.drop(columns=["split_role"])
    elif mutator == "metric_column":
        rows["hit_rate"] = 1.0
    elif mutator == "model_column":
        rows["model_version"] = "model_v1"
    elif mutator == "threshold_prediction_probability_importance_column":
        rows["prediction"] = 0.2
        rows["calibrated_probability"] = 0.3
        rows["feature_importance"] = 0.4
        rows["threshold_optimized"] = 0.5
    elif mutator == "stock_profile_column":
        rows["stock_profile_status"] = "ready"
    elif mutator == "buy_review_column":
        rows["real_buy_review_eligible"] = True
    elif mutator == "paper_column":
        rows["approved_for_paper"] = True
    elif mutator == "performance_column":
        rows["strategy_performance_validated"] = True
    elif mutator == "trading_column":
        rows["broker_order_id"] = "order"
    else:  # pragma: no cover
        raise AssertionError(f"unknown mutator: {mutator}")
    rows.to_csv(rows_path, index=False)


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "training_evaluation_v0_1"
