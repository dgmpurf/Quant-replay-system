from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system import cli
from quant_replay_system.forward_return_label import (
    FORWARD_RETURN_LABELS_CREATED,
    FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED,
    FORWARD_RETURN_LABEL_BENCHMARK_BLOCKED,
    FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED,
    FORWARD_RETURN_LABEL_INDUSTRY_BLOCKED,
    FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED,
    FORWARD_RETURN_LABEL_OVERCLAIM_BLOCKED,
    FORWARD_RETURN_LABEL_PRICE_INPUT_BLOCKED,
    FORWARD_RETURN_LABEL_SIDE_EFFECT_BLOCKED,
    FORWARD_RETURN_LABEL_WINDOW_BLOCKED,
    NO_FORWARD_RETURN_LABEL_INPUT,
    READY_FOR_FORWARD_RETURN_LABEL,
    EXACT_APPROVAL_TEXT,
    ForwardReturnLabelSettings,
    run_forward_return_label,
)
from quant_replay_system.forward_return_label_health import check_forward_return_label_health
from quant_replay_system.forward_return_label_index import build_forward_return_label_index
from quant_replay_system.forward_return_label_status import run_forward_return_label_status


def test_no_input_writes_required_artifacts_with_safe_defaults(tmp_path: Path) -> None:
    result = run_forward_return_label(ForwardReturnLabelSettings(output_dir=_output_dir(tmp_path)))

    assert result.status == NO_FORWARD_RETURN_LABEL_INPUT
    assert result.workflow_stage == "FORWARD_RETURN_LABEL_NO_INPUT"
    assert result.ready_for_forward_return_label is False
    assert result.forward_return_label_executed is False
    assert result.forward_return_label_artifacts_created is False
    assert result.forward_labels_allowed is False
    assert result.forward_labels_exist is False
    assert result.forward_return_labels_created is False
    _assert_downstream_flags_false(result)
    assert result.report_only is True
    assert result.diagnostic_only is True
    for key in _required_artifact_keys():
        assert result.artifact_paths[key].exists()
    metadata = _read_json(result.artifact_paths["metadata"])
    safety = _read_json(result.artifact_paths["safety_flags"])
    assert metadata["execution_status"] == NO_FORWARD_RETURN_LABEL_INPUT
    assert metadata["ready_for_forward_return_label"] is False
    for field in _downstream_false_fields():
        assert metadata[field] is False
        assert safety[field] is False
    assert pd.read_csv(result.artifact_paths["forward_return_label_rows"]).empty


@pytest.mark.parametrize(
    ("approval_text", "expected_status"),
    [
        ("", FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED),
        ("continue", FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED),
        ("make labels", FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED),
        ("compute forward returns", FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED),
        ("implement forward labels", FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED),
        ("go ahead", FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED),
        ("do the next task", FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED),
        ("Implement labels and train the model.", FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED),
        ("Implement labels and create stock_profile.", FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED),
        ("Implement labels and create buy-review eligibility.", FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED),
        ("Implement labels and apply paper approval.", FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED),
        ("Implement labels and validate strategy performance.", FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED),
        ("Implement labels and allow trading.", FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED),
    ],
)
def test_approval_wording_must_be_exact_and_narrow(
    tmp_path: Path,
    approval_text: str,
    expected_status: str,
) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.approval_manifest_path, {"approval_text": approval_text})

    result = run_forward_return_label(settings)

    assert result.status == expected_status
    assert result.ready_for_forward_return_label is False
    assert result.forward_return_labels_created is False
    _assert_downstream_flags_false(result)


@pytest.mark.parametrize(
    ("path_name", "patch", "expected_status"),
    [
        ("replay_decision_metadata_path", {"execution_status": "READY_FOR_REPLAY_DECISION_FREEZE"}, FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED),
        ("replay_decision_metadata_path", {"health_status": "FAIL"}, FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED),
        ("replay_decision_metadata_path", {"replay_decision_frozen": False}, FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED),
        ("replay_decision_metadata_path", {"replay_decisions_exist": False}, FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED),
        ("replay_decision_safety_flags_path", {"training_allowed": True}, FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED),
        ("replay_decision_safety_flags_path", {"stock_profile_created": True}, FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED),
        ("replay_decision_safety_flags_path", {"broker_api_called": True}, FORWARD_RETURN_LABEL_SIDE_EFFECT_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", {"training_result_created": True}, FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", {"data_raw_written": True}, FORWARD_RETURN_LABEL_SIDE_EFFECT_BLOCKED),
        ("overclaim_evidence_bundle_path", {"forward_labels_not_training_permission": False}, FORWARD_RETURN_LABEL_OVERCLAIM_BLOCKED),
        ("overclaim_evidence_bundle_path", {"strategy_performance_validated": True}, FORWARD_RETURN_LABEL_OVERCLAIM_BLOCKED),
    ],
)
def test_manifest_and_safety_gate_failures_block(
    tmp_path: Path,
    path_name: str,
    patch: dict[str, object],
    expected_status: str,
) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(getattr(settings, path_name), patch)

    result = run_forward_return_label(settings)

    assert result.status == expected_status
    assert result.forward_return_labels_created is False
    _assert_downstream_flags_false(result)


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("replay_decision_metadata_path", FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED),
        ("replay_decision_rows_path", FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED),
        ("replay_decision_evidence_index_path", FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED),
        ("replay_decision_safety_flags_path", FORWARD_RETURN_LABEL_FROZEN_DECISION_BLOCKED),
        ("price_input_csv_path", FORWARD_RETURN_LABEL_PRICE_INPUT_BLOCKED),
        ("label_window_rules_csv_path", FORWARD_RETURN_LABEL_WINDOW_BLOCKED),
        ("approval_manifest_path", FORWARD_RETURN_LABEL_AUTHORITY_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(
    tmp_path: Path,
    setting_name: str,
    expected_status: str,
) -> None:
    result = run_forward_return_label(replace(_happy_settings(tmp_path), **{setting_name: None}))

    assert result.status == expected_status
    assert result.ready_for_forward_return_label is False
    assert result.forward_return_labels_created is False


@pytest.mark.parametrize(
    ("column", "expected_status"),
    [
        ("forward_return", FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED),
        ("forward_return_label", FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED),
        ("training_score", FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED),
        ("model_weight", FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED),
        ("stock_profile_status", FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED),
        ("stock_profile_validated", FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED),
        ("real_buy_review_eligible", FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED),
        ("approved_for_paper", FORWARD_RETURN_LABEL_LEAKAGE_BLOCKED),
        ("strategy_performance_validated", FORWARD_RETURN_LABEL_OVERCLAIM_BLOCKED),
        ("order_id", FORWARD_RETURN_LABEL_SIDE_EFFECT_BLOCKED),
        ("broker_order_id", FORWARD_RETURN_LABEL_SIDE_EFFECT_BLOCKED),
        ("trade_id", FORWARD_RETURN_LABEL_SIDE_EFFECT_BLOCKED),
    ],
)
def test_replay_decision_rows_with_forbidden_columns_block(
    tmp_path: Path,
    column: str,
    expected_status: str,
) -> None:
    settings = _happy_settings(tmp_path)
    frame = pd.read_csv(settings.replay_decision_rows_path, dtype={"symbol": "string"})
    frame[column] = "unsafe"
    frame.to_csv(settings.replay_decision_rows_path, index=False)

    result = run_forward_return_label(settings)

    assert result.status == expected_status
    assert result.forward_return_labels_created is False


@pytest.mark.parametrize(
    "missing_column",
    ["source_hash", "revision_id", "available_time", "quality_status"],
)
def test_price_input_missing_required_lineage_columns_blocks(tmp_path: Path, missing_column: str) -> None:
    settings = _happy_settings(tmp_path)
    frame = pd.read_csv(settings.price_input_csv_path, dtype={"symbol": "string"})
    frame = frame.drop(columns=[missing_column])
    frame.to_csv(settings.price_input_csv_path, index=False)

    result = run_forward_return_label(settings)

    assert result.status == FORWARD_RETURN_LABEL_PRICE_INPUT_BLOCKED
    assert result.forward_return_labels_created is False


@pytest.mark.parametrize(
    ("requested_labels", "expected_status"),
    [
        ("unsupported_label", FORWARD_RETURN_LABEL_WINDOW_BLOCKED),
        ("benchmark_relative_return_5d", FORWARD_RETURN_LABEL_BENCHMARK_BLOCKED),
        ("industry_relative_return_5d", FORWARD_RETURN_LABEL_INDUSTRY_BLOCKED),
    ],
)
def test_unsupported_or_unmapped_label_requests_block(
    tmp_path: Path,
    requested_labels: str,
    expected_status: str,
) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.forward_label_request_manifest_path, {"label_names": requested_labels})
    if expected_status == FORWARD_RETURN_LABEL_BENCHMARK_BLOCKED:
        settings.benchmark_mapping_csv_path.unlink()
    if expected_status == FORWARD_RETURN_LABEL_INDUSTRY_BLOCKED:
        settings.industry_mapping_csv_path.unlink()

    result = run_forward_return_label(settings)

    assert result.status == expected_status


@pytest.mark.parametrize("price_patch", [{"close": ""}, {"trade_date": "2024-04-02"}])
def test_missing_start_or_end_price_blocks(tmp_path: Path, price_patch: dict[str, object]) -> None:
    settings = _happy_settings(tmp_path)
    frame = pd.read_csv(settings.price_input_csv_path, dtype={"symbol": "string"})
    if "close" in price_patch:
        frame.loc[frame["trade_date"] == "2024-04-02", "close"] = ""
    else:
        frame = frame.loc[frame["trade_date"] != "2024-04-09"]
    frame.to_csv(settings.price_input_csv_path, index=False)

    result = run_forward_return_label(settings)

    assert result.status == FORWARD_RETURN_LABEL_PRICE_INPUT_BLOCKED


def test_happy_path_without_allow_reaches_ready_and_creates_no_labels(tmp_path: Path) -> None:
    result = run_forward_return_label(_happy_settings(tmp_path))

    assert result.status == READY_FOR_FORWARD_RETURN_LABEL
    assert result.ready_for_forward_return_label is True
    assert result.forward_return_label_executed is False
    assert result.forward_return_label_artifacts_created is False
    assert result.forward_labels_allowed is False
    assert result.forward_labels_exist is False
    assert result.forward_return_labels_created is False
    assert pd.read_csv(result.artifact_paths["forward_return_label_rows"]).empty
    _assert_downstream_flags_false(result)


def test_happy_path_with_explicit_allow_creates_report_only_forward_labels(tmp_path: Path) -> None:
    result = run_forward_return_label(replace(_happy_settings(tmp_path), allow_forward_return_label=True))

    assert result.status == FORWARD_RETURN_LABELS_CREATED
    assert result.workflow_stage == FORWARD_RETURN_LABELS_CREATED
    assert result.ready_for_forward_return_label is True
    assert result.forward_return_label_executed is True
    assert result.forward_return_label_artifacts_created is True
    assert result.forward_labels_allowed is True
    assert result.forward_labels_exist is True
    assert result.forward_return_labels_created is True
    assert result.forward_return_label_artifact_path.endswith("forward_return_label_rows.csv")
    _assert_downstream_flags_false(result)

    labels = pd.read_csv(result.artifact_paths["forward_return_label_rows"], dtype={"symbol": "string"})
    assert set(labels["label_name"]) == {
        "forward_return_5d",
        "max_drawdown_5d",
        "max_runup_5d",
        "benchmark_relative_return_5d",
        "industry_relative_return_5d",
    }
    row = labels.loc[labels["label_name"] == "forward_return_5d"].iloc[0]
    assert row["symbol"] == "000001"
    assert row["replay_decision_id"] == "decision_000001_20240402"
    assert row["replay_decision_freeze_run_id"] == "freeze_abc123"
    assert row["actual_replay_execution_run_id"] == "actual_001"
    assert row["source_active_input_creation_run_id"] == "active_001"
    assert row["source_real_replay_precheck_run_id"] == "precheck_001"
    assert row["price_source_hash"] == "price_hash"
    assert row["price_revision_id"] == "price_rev"
    assert row["price_quality_status"] == "PASS"
    assert row["suspended_days_count"] == 1
    assert row["limit_up_days_count"] == 1
    assert row["limit_down_days_count"] == 1
    assert row["report_only"] is True or str(row["report_only"]) == "True"
    assert row["diagnostic_only"] is True or str(row["diagnostic_only"]) == "True"
    assert row["forward_return"] == pytest.approx(0.10)
    assert row["benchmark_relative_return"] == pytest.approx(0.10 - (3100 / 3000 - 1))
    assert row["industry_relative_return"] == pytest.approx(0.10 - (2200 / 2000 - 1))

    drawdown = labels.loc[labels["label_name"] == "max_drawdown_5d"].iloc[0]
    runup = labels.loc[labels["label_name"] == "max_runup_5d"].iloc[0]
    assert drawdown["max_drawdown"] == pytest.approx(-0.05)
    assert runup["max_runup"] == pytest.approx(0.16)

    forbidden = _forbidden_label_columns()
    assert not forbidden.intersection(labels.columns)
    metadata = _read_json(result.artifact_paths["metadata"])
    safety = _read_json(result.artifact_paths["safety_flags"])
    assert metadata["source_replay_decision_freeze_run_id"] == "freeze_abc123"
    assert metadata["labels_joined_after_freeze"] is True
    assert metadata["labels_excluded_from_decision_rows"] is True
    assert metadata["strategy_performance_validated"] is False
    assert safety["forward_labels_allowed"] is True
    assert safety["training_allowed"] is False
    report = result.artifact_paths["report"].read_text(encoding="utf-8")
    assert "not training" in report
    assert "not stock_profile" in report
    assert "not buy-review" in report
    assert "not paper approval" in report
    assert "not performance validation" in report
    assert "not trading" in report


def test_output_path_outside_manual_diagnostics_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_forward_return_label(ForwardReturnLabelSettings(output_dir=tmp_path / "unsafe"))


def test_cli_forward_return_label_runs_no_input(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "forward-return-label",
            "--output-dir",
            str(_output_dir(tmp_path)),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert f"status: {NO_FORWARD_RETURN_LABEL_INPUT}" in completed.stdout
    assert "ready_for_forward_return_label: False" in completed.stdout
    assert "forward_return_labels_created: False" in completed.stdout
    assert "training_allowed: False" in completed.stdout
    assert "stock_profile_allowed: False" in completed.stdout
    assert "strategy_performance_validated: False" in completed.stdout
    assert "trading_allowed: False" in completed.stdout


def test_cli_happy_paths_respect_explicit_allow(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    ready = _run_cli_with_settings(settings, allow=False)
    created = _run_cli_with_settings(replace(settings, output_dir=_output_dir(tmp_path) / "allow"), allow=True)

    assert f"status: {READY_FOR_FORWARD_RETURN_LABEL}" in ready.stdout
    assert "forward_return_label_artifacts_created: False" in ready.stdout
    assert "forward_labels_allowed: False" in ready.stdout
    assert f"status: {FORWARD_RETURN_LABELS_CREATED}" in created.stdout
    assert "forward_return_label_artifacts_created: True" in created.stdout
    assert "forward_labels_allowed: True" in created.stdout
    assert "training_allowed: False" in created.stdout
    assert "stock_profile_allowed: False" in created.stdout
    assert "trading_allowed: False" in created.stdout


def test_core_views_research_status_docs_checkpoint_and_source_note_are_present_without_project_source() -> None:
    parser = cli.build_parser()
    command_names = {action.dest for action in parser._subparsers._group_actions[0]._choices_actions}
    assert "forward-return-label" in command_names
    assert "forward-return-label-index" in command_names
    assert "forward-return-label-health" in command_names
    assert "forward-return-label-status" in command_names
    assert "research-status" in command_names
    assert Path("docs/forward_return_label.md").exists()
    assert Path("docs/release_checkpoint_v1.44.0.md").exists()
    assert not Path("docs/release_checkpoint_v1.45.0.md").exists()
    assert Path("SOURCE_UPDATE_NOTES_v1_44_0.md").exists()
    assert not Path("SOURCE_UPDATE_NOTES_v1_45_0.md").exists()
    assert not Path("docs/project_sources").exists()
    docs_text = Path("docs/forward_return_label.md").read_text(encoding="utf-8")
    checkpoint_text = Path("docs/release_checkpoint_v1.44.0.md").read_text(encoding="utf-8")
    source_notes_text = Path("SOURCE_UPDATE_NOTES_v1_44_0.md").read_text(encoding="utf-8")
    for text in [docs_text, checkpoint_text, source_notes_text]:
        assert "report-only" in text
        assert "not training" in text
        assert "not stock_profile" in text
        assert "not buy-review eligibility" in text
        assert "not paper approval" in text
        assert "not performance validation" in text
        assert "not trading" in text


def test_forward_return_label_index_discovers_no_input_ready_and_created_artifacts(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    no_input = run_forward_return_label(ForwardReturnLabelSettings(output_dir=root))
    ready = run_forward_return_label(replace(_happy_settings(tmp_path), output_dir=root))
    created = run_forward_return_label(replace(_happy_settings(tmp_path), output_dir=root, allow_forward_return_label=True))

    result = build_forward_return_label_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 3
    frame = result.index_frame
    assert set(frame["status"]) == {NO_FORWARD_RETURN_LABEL_INPUT, READY_FOR_FORWARD_RETURN_LABEL, FORWARD_RETURN_LABELS_CREATED}
    created_row = frame.loc[frame["status"] == FORWARD_RETURN_LABELS_CREATED].iloc[0]
    assert created_row["forward_return_label_run_id"] == created.forward_return_label_run_id
    assert created_row["source_replay_decision_freeze_run_id"] == "freeze_abc123"
    assert created_row["replay_decision_frozen"] is True
    assert created_row["replay_decisions_exist"] is True
    assert created_row["forward_return_label_executed"] is True
    assert created_row["forward_return_label_artifacts_created"] is True
    assert created_row["forward_labels_allowed"] is True
    assert created_row["forward_return_labels_created"] is True
    assert created_row["label_row_count"] == 5
    assert created_row["symbol_count"] == 1
    assert created_row["replay_decision_count"] == 1
    assert "forward_return_5d" in created_row["label_name_set"]
    for field in _downstream_false_fields():
        assert created_row[field] is False
    assert frame.loc[frame["status"] == NO_FORWARD_RETURN_LABEL_INPUT].iloc[0]["forward_return_label_run_id"] == no_input.forward_return_label_run_id
    assert frame.loc[frame["status"] == READY_FOR_FORWARD_RETURN_LABEL].iloc[0]["forward_return_label_run_id"] == ready.forward_return_label_run_id


@pytest.mark.parametrize(
    ("settings_factory", "expected_status"),
    [
        (lambda tmp_path: ForwardReturnLabelSettings(output_dir=_output_dir(tmp_path)), NO_FORWARD_RETURN_LABEL_INPUT),
        (lambda tmp_path: _happy_settings(tmp_path), READY_FOR_FORWARD_RETURN_LABEL),
        (lambda tmp_path: replace(_happy_settings(tmp_path), allow_forward_return_label=True), FORWARD_RETURN_LABELS_CREATED),
    ],
)
def test_forward_return_label_health_passes_valid_report_only_artifacts(
    tmp_path: Path,
    settings_factory: object,
    expected_status: str,
) -> None:
    settings = settings_factory(tmp_path)
    run_forward_return_label(settings)

    root = settings.output_dir
    result = check_forward_return_label_health(root=root, output_dir=root / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.error_count == 0
    indexed = build_forward_return_label_index(root=root, output_dir=root / "index").index_frame.iloc[0]
    assert indexed["status"] == expected_status


@pytest.mark.parametrize(
    ("mutator", "issue_code"),
    [
        ("delete_created_rows", "LABELS_CREATED_WITHOUT_ROWS"),
        ("rows_with_ready_status", "ROWS_EXIST_WITHOUT_LABELS_CREATED_STATUS"),
        ("invalid_label_name", "LABEL_NAME_OUTSIDE_ALLOWED_SET"),
        ("drop_lineage", "LABEL_ROWS_REQUIRED_COLUMNS_MISSING"),
        ("drop_price_lineage", "LABEL_ROWS_REQUIRED_COLUMNS_MISSING"),
        ("training_column", "LABEL_ROWS_FORBIDDEN_TRAINING_COLUMNS"),
        ("model_column", "LABEL_ROWS_FORBIDDEN_MODEL_COLUMNS"),
        ("stock_profile_column", "LABEL_ROWS_FORBIDDEN_STOCK_PROFILE_COLUMNS"),
        ("buy_review_column", "LABEL_ROWS_FORBIDDEN_BUY_REVIEW_COLUMNS"),
        ("paper_column", "LABEL_ROWS_FORBIDDEN_PAPER_APPROVAL_COLUMNS"),
        ("performance_column", "LABEL_ROWS_FORBIDDEN_PERFORMANCE_COLUMNS"),
        ("trading_column", "LABEL_ROWS_FORBIDDEN_TRADING_COLUMNS"),
    ],
)
def test_forward_return_label_health_fails_unsafe_or_malformed_label_rows(
    tmp_path: Path,
    mutator: str,
    issue_code: str,
) -> None:
    settings = replace(_happy_settings(tmp_path), allow_forward_return_label=True)
    run = run_forward_return_label(settings)
    _mutate_label_artifact(run.artifact_paths["artifact_dir"], mutator)

    health = check_forward_return_label_health(root=settings.output_dir, output_dir=settings.output_dir / "health")

    assert health.status == "FAIL"
    assert issue_code in set(health.health_frame["issue_code"])


@pytest.mark.parametrize(
    "flag",
    [
        "training_allowed",
        "weights_trained",
        "training_result_created",
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
def test_forward_return_label_health_fails_unsafe_metadata_or_safety_flags(tmp_path: Path, flag: str) -> None:
    settings = replace(_happy_settings(tmp_path), allow_forward_return_label=True)
    run = run_forward_return_label(settings)
    _patch_json(run.artifact_paths["metadata"], {flag: True})
    _patch_json(run.artifact_paths["safety_flags"], {flag: True})

    health = check_forward_return_label_health(root=settings.output_dir, output_dir=settings.output_dir / "health")

    assert health.status == "FAIL"
    assert f"{flag.upper()}_UNEXPECTED" in set(health.health_frame["issue_code"])


def test_forward_return_label_status_reports_no_input_ready_and_created_states(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    no_input = run_forward_return_label(ForwardReturnLabelSettings(output_dir=root))
    no_input_status = run_forward_return_label_status(root=root, output_dir=root / "status_no_input")
    assert no_input_status.latest_forward_return_label_run_id == no_input.forward_return_label_run_id
    assert no_input_status.workflow_stage == "FORWARD_RETURN_LABEL_NO_INPUT"
    assert no_input_status.forward_return_labels_created is False

    ready = run_forward_return_label(replace(_happy_settings(tmp_path), output_dir=root))
    ready_status = run_forward_return_label_status(root=root, output_dir=root / "status_ready")
    assert ready_status.latest_forward_return_label_run_id == ready.forward_return_label_run_id
    assert ready_status.workflow_stage == READY_FOR_FORWARD_RETURN_LABEL
    assert ready_status.ready_for_forward_return_label is True
    assert ready_status.forward_return_label_artifacts_created is False

    created = run_forward_return_label(replace(_happy_settings(tmp_path), output_dir=root, allow_forward_return_label=True))
    created_status = run_forward_return_label_status(root=root, output_dir=root / "status_created")
    assert created_status.latest_forward_return_label_run_id == created.forward_return_label_run_id
    assert created_status.workflow_stage == FORWARD_RETURN_LABELS_CREATED
    assert created_status.forward_return_labels_created is True
    assert created_status.label_row_count == 5
    assert "forward_return_5d" in created_status.label_name_set
    assert created_status.training_allowed is False
    assert created_status.stock_profile_allowed is False
    assert created_status.trading_allowed is False
    text = created_status.safety_statement
    assert "report-only" in text
    assert "future outcome labels only" in text
    assert "not train weights" in text
    assert "not create training_result" in text
    assert "not create stock_profile" in text
    assert "not create buy-review eligibility" in text
    assert "not apply paper approval" in text
    assert "not validate strategy performance" in text
    assert "not authorize trading" in text


def test_forward_return_label_view_cli_commands_run(tmp_path: Path) -> None:
    settings = replace(_happy_settings(tmp_path), allow_forward_return_label=True)
    run_forward_return_label(settings)

    index = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "forward-return-label-index",
            "--root",
            str(settings.output_dir),
            "--output-dir",
            str(settings.output_dir / "index"),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    health = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "forward-return-label-health",
            "--root",
            str(settings.output_dir),
            "--output-dir",
            str(settings.output_dir / "health"),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    status = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "forward-return-label-status",
            "--root",
            str(settings.output_dir),
            "--output-dir",
            str(settings.output_dir / "status"),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "artifact_count: 1" in index.stdout
    assert "status: PASS" in health.stdout
    assert f"latest_forward_return_label_run_id: {build_forward_return_label_index(root=settings.output_dir, output_dir=settings.output_dir / 'index2').index_frame.iloc[0]['forward_return_label_run_id']}" in status.stdout
    assert "forward_return_labels_created: True" in status.stdout
    assert "report-only" in status.stdout
    assert "not train weights" in status.stdout


def _happy_settings(tmp_path: Path) -> ForwardReturnLabelSettings:
    root = _fixture_root(tmp_path)
    root.mkdir(parents=True, exist_ok=True)
    metadata = _write_json(root / "replay_decision_metadata.json", _replay_decision_metadata())
    rows = _write_replay_decision_rows(root / "replay_decision_rows.csv")
    evidence = _write_csv(
        root / "replay_decision_evidence_index.csv",
        [
            {
                "replay_decision_id": "decision_000001_20240402",
                "source_id": "source_szse_1815",
                "source_hash": "evidence_hash",
                "revision_id": "evidence_rev",
                "available_time": "2024-04-02T15:30:00+08:00",
            }
        ],
    )
    safety = _write_json(root / "replay_decision_safety_flags.json", _safe_flags())
    approval = _write_json(root / "approval.json", {"approval_text": EXACT_APPROVAL_TEXT})
    request = _write_json(
        root / "request.json",
        {"forward_return_label_core_requested": True, "report_only": True, "label_names": "forward_return_5d;max_drawdown_5d;max_runup_5d;benchmark_relative_return_5d;industry_relative_return_5d"},
    )
    prices = _write_price_rows(root / "prices.csv")
    benchmarks = _write_benchmark_rows(root / "benchmarks.csv")
    industries = _write_industry_rows(root / "industries.csv")
    benchmark_mapping = _write_csv(root / "benchmark_mapping.csv", [{"symbol": "000001", "benchmark_symbol": "000300"}])
    industry_mapping = _write_csv(
        root / "industry_mapping.csv",
        [{"symbol": "000001", "industry_code": "BANK", "industry_name": "Banking"}],
    )
    windows = _write_csv(
        root / "label_windows.csv",
        [
            {"label_name": "forward_return_5d", "horizon_trading_days": 5},
            {"label_name": "max_drawdown_5d", "horizon_trading_days": 5},
            {"label_name": "max_runup_5d", "horizon_trading_days": 5},
            {"label_name": "benchmark_relative_return_5d", "horizon_trading_days": 5},
            {"label_name": "industry_relative_return_5d", "horizon_trading_days": 5},
        ],
    )
    leakage = _write_json(root / "leakage.json", _safe_flags())
    overclaim = _write_json(
        root / "overclaim.json",
        {
            "forward_labels_not_training_permission": True,
            "forward_labels_not_stock_profile_permission": True,
            "forward_labels_not_buy_review_eligibility": True,
            "forward_labels_not_paper_approval": True,
            "forward_labels_not_performance_validation": True,
            "forward_labels_not_trading_authorization": True,
            "strategy_performance_validated": False,
        },
    )
    return ForwardReturnLabelSettings(
        replay_decision_freeze_artifact_path=root,
        replay_decision_metadata_path=metadata,
        replay_decision_rows_path=rows,
        replay_decision_evidence_index_path=evidence,
        replay_decision_safety_flags_path=safety,
        approval_manifest_path=approval,
        forward_label_request_manifest_path=request,
        price_input_csv_path=prices,
        benchmark_input_csv_path=benchmarks,
        industry_input_csv_path=industries,
        benchmark_mapping_csv_path=benchmark_mapping,
        industry_mapping_csv_path=industry_mapping,
        label_window_rules_csv_path=windows,
        leakage_side_effect_evidence_bundle_path=leakage,
        overclaim_evidence_bundle_path=overclaim,
        output_dir=_output_dir(tmp_path),
    )


def _replay_decision_metadata() -> dict[str, object]:
    payload = {
        "forward_return_label_run_id": "",
        "replay_decision_freeze_run_id": "freeze_abc123",
        "execution_status": "REPLAY_DECISION_FROZEN",
        "workflow_stage": "REPLAY_DECISION_FROZEN",
        "health_status": "PASS",
        "replay_decision_frozen": True,
        "replay_decisions_exist": True,
        "replay_decision_artifact_path": "replay_decision_rows.csv",
        "source_actual_replay_execution_run_id": "actual_001",
        "source_active_input_creation_run_id": "active_001",
        "source_real_replay_precheck_run_id": "precheck_001",
        "replay_as_of_date": "2024-04-02",
        "source_hash_coverage": "COMPLETE",
        "revision_id_coverage": "COMPLETE",
        "available_time_policy": "ALL_AVAILABLE_TIME_LTE_REPLAY_DECISION_TIME",
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update(_safe_flags())
    return payload


def _write_replay_decision_rows(path: Path) -> Path:
    return _write_csv(
        path,
        [
            {
                "replay_decision_id": "decision_000001_20240402",
                "replay_decision_freeze_run_id": "freeze_abc123",
                "actual_replay_execution_run_id": "actual_001",
                "source_active_input_creation_run_id": "active_001",
                "source_real_replay_precheck_run_id": "precheck_001",
                "replay_as_of_date": "2024-04-02",
                "symbol": "000001",
                "instrument_type": "STOCK",
                "decision_label": "WATCH",
                "generated_at": "2024-04-02T15:30:00+08:00",
                "frozen_at": "2024-04-02T15:31:00+08:00",
                "report_only": True,
                "diagnostic_only": True,
            }
        ],
    )


def _write_price_rows(path: Path) -> Path:
    rows = []
    values = [
        ("2024-04-02", 100, 105, 95, 100, False, False, False),
        ("2024-04-03", 101, 106, 98, 102, False, False, False),
        ("2024-04-04", 102, 108, 99, 104, False, True, False),
        ("2024-04-05", 104, 109, 101, 106, True, False, False),
        ("2024-04-08", 106, 112, 103, 108, False, False, True),
        ("2024-04-09", 108, 116, 106, 110, False, False, False),
    ]
    for date, open_, high, low, close, suspended, limit_up, limit_down in values:
        rows.append(
            {
                "symbol": "000001",
                "trade_date": date,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": 1000,
                "amount": 100000,
                "adjustment_factor": 1.0,
                "suspended_flag": suspended,
                "limit_up_flag": limit_up,
                "limit_down_flag": limit_down,
                "source_id": "price_source",
                "source_hash": "price_hash",
                "revision_id": "price_rev",
                "available_time": f"{date}T15:30:00+08:00",
                "quality_status": "PASS",
            }
        )
    return _write_csv(path, rows)


def _write_benchmark_rows(path: Path) -> Path:
    return _write_csv(
        path,
        [
            {
                "benchmark_symbol": "000300",
                "trade_date": date,
                "close": close,
                "source_id": "benchmark_source",
                "source_hash": "benchmark_hash",
                "revision_id": "benchmark_rev",
                "available_time": f"{date}T15:30:00+08:00",
                "quality_status": "PASS",
            }
            for date, close in [("2024-04-02", 3000), ("2024-04-09", 3100)]
        ],
    )


def _write_industry_rows(path: Path) -> Path:
    return _write_csv(
        path,
        [
            {
                "industry_code": "BANK",
                "industry_name": "Banking",
                "trade_date": date,
                "close": close,
                "source_id": "industry_source",
                "source_hash": "industry_hash",
                "revision_id": "industry_rev",
                "available_time": f"{date}T15:30:00+08:00",
                "quality_status": "PASS",
            }
            for date, close in [("2024-04-02", 2000), ("2024-04-09", 2200)]
        ],
    )


def _safe_flags() -> dict[str, object]:
    return {field: False for field in _downstream_false_fields()} | {
        "message_sent": False,
        "llm_api_called": False,
        "external_api_called": False,
        "cache_mutated": False,
        "data_raw_written": False,
        "data_processed_written": False,
        "data_cache_written": False,
        "current_candidates_run": False,
        "snapshot_built": False,
        "signal_semantics_changed": False,
    }


def _required_artifact_keys() -> list[str]:
    return [
        "metadata",
        "report",
        "forward_return_label_rows",
        "forward_return_label_price_input_index",
        "forward_return_label_benchmark_index",
        "forward_return_label_industry_index",
        "safety_flags",
        "precondition_results",
        "lineage_results",
        "authority_results",
        "frozen_replay_decision_results",
        "price_input_results",
        "label_window_results",
        "benchmark_industry_results",
        "leakage_side_effect_guard_results",
        "overclaim_guard_results",
        "recommended_next_task",
    ]


def _downstream_false_fields() -> list[str]:
    return [
        "training_allowed",
        "weights_trained",
        "training_result_created",
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
    ]


def _forbidden_label_columns() -> set[str]:
    return {
        "training_score",
        "model_weight",
        "model_version",
        "threshold_optimized",
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
    for field in _downstream_false_fields():
        assert getattr(result, field) is False


def _run_cli_with_settings(settings: ForwardReturnLabelSettings, *, allow: bool) -> subprocess.CompletedProcess[str]:
    args = [
        sys.executable,
        "-m",
        "quant_replay_system.cli",
        "forward-return-label",
        "--replay-decision-freeze-artifact-path",
        str(settings.replay_decision_freeze_artifact_path),
        "--replay-decision-metadata-path",
        str(settings.replay_decision_metadata_path),
        "--replay-decision-rows-path",
        str(settings.replay_decision_rows_path),
        "--replay-decision-evidence-index-path",
        str(settings.replay_decision_evidence_index_path),
        "--replay-decision-safety-flags-path",
        str(settings.replay_decision_safety_flags_path),
        "--approval-manifest-path",
        str(settings.approval_manifest_path),
        "--forward-label-request-manifest-path",
        str(settings.forward_label_request_manifest_path),
        "--price-input-csv-path",
        str(settings.price_input_csv_path),
        "--benchmark-input-csv-path",
        str(settings.benchmark_input_csv_path),
        "--industry-input-csv-path",
        str(settings.industry_input_csv_path),
        "--benchmark-mapping-csv-path",
        str(settings.benchmark_mapping_csv_path),
        "--industry-mapping-csv-path",
        str(settings.industry_mapping_csv_path),
        "--label-window-rules-csv-path",
        str(settings.label_window_rules_csv_path),
        "--leakage-side-effect-evidence-bundle-path",
        str(settings.leakage_side_effect_evidence_bundle_path),
        "--overclaim-evidence-bundle-path",
        str(settings.overclaim_evidence_bundle_path),
        "--output-dir",
        str(settings.output_dir),
    ]
    if allow:
        args.append("--allow-forward-return-label")
    return subprocess.run(args, check=True, capture_output=True, text=True, env={**os.environ, "PYTHONPATH": "src"})


def _write_csv(path: Path, rows: list[dict[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _write_json(path: Path, payload: dict[str, object]) -> Path:
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


def _mutate_label_artifact(artifact_dir: Path, mutator: str) -> None:
    rows_path = artifact_dir / "forward_return_label_rows.csv"
    metadata_path = artifact_dir / "metadata.json"
    rows = pd.read_csv(rows_path, dtype={"symbol": "string"})
    if mutator == "delete_created_rows":
        rows_path.unlink()
        return
    if mutator == "rows_with_ready_status":
        _patch_json(metadata_path, {"execution_status": READY_FOR_FORWARD_RETURN_LABEL, "status": READY_FOR_FORWARD_RETURN_LABEL})
        return
    if mutator == "invalid_label_name":
        rows.loc[0, "label_name"] = "bad_label"
    elif mutator == "drop_lineage":
        rows = rows.drop(columns=["replay_decision_freeze_run_id"])
    elif mutator == "drop_price_lineage":
        rows = rows.drop(columns=["price_source_hash"])
    elif mutator == "training_column":
        rows["training_score"] = 1.0
    elif mutator == "model_column":
        rows["model_version"] = "model"
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
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "forward_return_label_v0_1"


def _fixture_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "forward_return_label_fixture_v0_1"
