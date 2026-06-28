from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.replay_decision_schema_fixture import (
    FORBIDDEN_METADATA_FALSE_FLAGS,
    REPLAY_DECISION_SCHEMA_FIXTURE_CREATED,
    REQUIRED_REPLAY_DECISION_FIELDS,
    build_replay_decision_schema_fixture,
)
from quant_replay_system.replay_decision_schema_fixture_health import check_replay_decision_schema_fixture_health
from quant_replay_system.replay_decision_schema_fixture_index import (
    NO_REPLAY_DECISION_SCHEMA_FIXTURE,
    build_replay_decision_schema_fixture_index,
)
from quant_replay_system.replay_decision_schema_fixture_status import (
    REPLAY_DECISION_SCHEMA_FIXTURE_INVALID,
    run_replay_decision_schema_fixture_status,
)


def test_index_safe_empty_behavior(tmp_path: Path) -> None:
    result = build_replay_decision_schema_fixture_index(root=tmp_path / "missing", output_dir=tmp_path / "index")

    assert result.artifact_count == 0
    assert result.latest_run_id == ""
    assert result.latest_status == "NO_INPUT"
    assert result.latest_workflow_stage == NO_REPLAY_DECISION_SCHEMA_FIXTURE
    assert result.latest_health_status == "PASS"
    assert result.index_frame.empty
    assert result.artifact_paths["index_csv"].exists()


def test_index_ignores_view_dirs_discovers_fixture_and_preserves_numeric_run_id(tmp_path: Path) -> None:
    fixture = build_replay_decision_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["replay_decision_schema_fixture_id"] = "522962104398"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")
    for name in ["index", "health", "status"]:
        (tmp_path / name).mkdir()

    result = build_replay_decision_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")
    row = result.index_frame.loc[0]

    assert result.artifact_count == 1
    assert result.latest_run_id == "522962104398"
    assert isinstance(row["replay_decision_schema_fixture_id"], str)
    assert row["replay_decision_schema_fixture_id"] == "522962104398"
    assert result.latest_status == "PASS"
    assert result.latest_workflow_stage == REPLAY_DECISION_SCHEMA_FIXTURE_CREATED
    assert result.latest_health_status == "PASS"
    assert row["expected_artifacts"] == 13
    assert row["decision_count"] == 10
    assert row["validation_issue_count"] == 0
    assert row["metadata_path"] == str(fixture.artifact_paths["metadata"])
    assert row["schema_fields_path"] == str(fixture.artifact_paths["schema_fields"])
    assert row["fixture_rows_path"] == str(fixture.artifact_paths["fixture_rows"])
    assert row["evidence_bundle_matrix_path"] == str(fixture.artifact_paths["evidence_bundle_matrix"])
    assert row["replay_decision_schema_fixture_created"] is True
    assert row["replay_decision_rows_created"] is True
    assert row["report_only"] is True
    assert row["diagnostic_only"] is True
    assert row["replay_evidence_bundle_schema_fixture_used"] is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert row[flag] is False
    written = pd.read_csv(result.artifact_paths["index_csv"], dtype=str)
    assert written.loc[0, "replay_decision_schema_fixture_id"] == "522962104398"


def test_health_passes_for_empty_and_valid_fixture_runs(tmp_path: Path) -> None:
    empty = check_replay_decision_schema_fixture_health(root=tmp_path / "missing", output_dir=tmp_path / "empty")
    assert empty.status == "PASS"
    assert empty.checked_artifact_count == 0
    assert empty.issue_count == 0

    build_replay_decision_schema_fixture(output_dir=tmp_path)
    result = check_replay_decision_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0
    assert result.artifact_paths["health_csv"].exists()


def test_health_fails_when_metadata_unreadable_or_required_artifact_missing(tmp_path: Path) -> None:
    fixture = build_replay_decision_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["metadata"].write_text("{not-json", encoding="utf-8")

    result = check_replay_decision_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_bad_json")
    assert "METADATA_UNREADABLE" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_replay_decision_schema_fixture(output_dir=tmp_path)
    fixture.artifact_paths["fixture_rows"].unlink()

    result = check_replay_decision_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_missing")
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fails_when_status_or_required_columns_are_invalid(tmp_path: Path) -> None:
    fixture = build_replay_decision_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["status"] = "MAYBE"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_replay_decision_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_status")
    assert "UNKNOWN_STATUS" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_replay_decision_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).drop(columns=["available_time_max"])
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_replay_decision_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_rows")
    assert "FIXTURE_ROWS_REQUIRED_COLUMNS_MISSING" in _issue_codes(result)

    shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    fixture = build_replay_decision_schema_fixture(output_dir=tmp_path)
    fields = pd.read_csv(fixture.artifact_paths["schema_fields"], dtype=str)
    fields = fields[fields["field_name"] != "available_time_max"]
    fields.to_csv(fixture.artifact_paths["schema_fields"], index=False)

    result = check_replay_decision_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health_fields")
    assert "SCHEMA_FIELDS_REQUIRED_FIELDS_MISSING" in _issue_codes(result)


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (lambda rows: rows.iloc[:-1], "DECISION_COUNT_NOT_10"),
        (
            lambda rows: rows.assign(
                replay_decision_id=rows["replay_decision_id"].where(rows.index != 1, rows.loc[0, "replay_decision_id"])
            ),
            "REPLAY_DECISION_ID_NOT_UNIQUE",
        ),
        (
            lambda rows: rows.assign(replay_decision_time=rows["replay_decision_time"].where(rows.index != 0, "")),
            "REPLAY_DECISION_TIME_MISSING",
        ),
        (lambda rows: rows.assign(entity_id=rows["entity_id"].where(rows.index != 0, "")), "ENTITY_CONTEXT_MISSING"),
        (lambda rows: rows.assign(symbol=rows["symbol"].where(rows.index != 0, "")), "ENTITY_CONTEXT_MISSING"),
        (
            lambda rows: rows.assign(instrument_type=rows["instrument_type"].where(rows.index != 0, "")),
            "ENTITY_CONTEXT_MISSING",
        ),
        (
            lambda rows: rows.assign(replay_evidence_bundle_id=rows["replay_evidence_bundle_id"].where(rows.index != 0, "")),
            "REPLAY_EVIDENCE_BUNDLE_ID_MISSING",
        ),
        (
            lambda rows: rows.assign(replay_evidence_bundle_status=rows["replay_evidence_bundle_status"].where(rows.index != 0, "WARN")),
            "ELIGIBLE_BUNDLE_STATUS_NOT_PASS",
        ),
        (
            lambda rows: rows.assign(replay_evidence_bundle_health_status=rows["replay_evidence_bundle_health_status"].where(rows.index != 0, "WARN")),
            "ELIGIBLE_BUNDLE_HEALTH_NOT_PASS",
        ),
        (
            lambda rows: rows.assign(replay_evidence_bundle_workflow_stage=rows["replay_evidence_bundle_workflow_stage"].where(rows.index != 0, "WRONG_STAGE")),
            "ELIGIBLE_BUNDLE_STAGE_INVALID",
        ),
        (
            lambda rows: rows.assign(available_time_max=rows["available_time_max"].where(rows.index != 0, "2025-01-01T09:30:00")),
            "ELIGIBLE_AVAILABLE_TIME_AFTER_DECISION_TIME",
        ),
        (lambda rows: rows.assign(future_label_excluded="False"), "FUTURE_LABELS_NOT_EXCLUDED"),
        (lambda rows: rows.assign(future_outcome_excluded="False"), "FUTURE_OUTCOMES_NOT_EXCLUDED"),
        (lambda rows: rows.assign(future_return_excluded="False"), "FUTURE_RETURNS_NOT_EXCLUDED"),
        (lambda rows: rows.assign(future_revision_excluded="False"), "FUTURE_REVISIONS_NOT_EXCLUDED"),
        (lambda rows: rows.assign(metrics_excluded="False"), "OUTPUTS_NOT_EXCLUDED"),
        (lambda rows: rows.assign(training_output_excluded="False"), "OUTPUTS_NOT_EXCLUDED"),
        (lambda rows: rows.assign(model_output_excluded="False"), "OUTPUTS_NOT_EXCLUDED"),
        (lambda rows: rows.assign(stock_profile_output_excluded="False"), "OUTPUTS_NOT_EXCLUDED"),
        (lambda rows: rows.assign(paper_approval_excluded="False"), "OUTPUTS_NOT_EXCLUDED"),
        (lambda rows: rows.assign(buy_review_output_excluded="False"), "OUTPUTS_NOT_EXCLUDED"),
        (lambda rows: rows.assign(decision_label=rows["decision_label"].where(rows.index != 0, "BUY_NOW")), "DECISION_LABEL_INVALID"),
        (
            lambda rows: rows.assign(freeze_status=rows["freeze_status"].where(rows.index != 0, "REAL_FROZEN")),
            "FREEZE_STATUS_INVALID",
        ),
        (
            lambda rows: rows.assign(mutation_allowed=rows["mutation_allowed"].where(rows.index != 0, "True")),
            "FROZEN_ROW_MUTATION_ALLOWED",
        ),
        (
            lambda rows: rows.assign(decision_hash=rows["decision_hash"].where(rows.index != 0, "")),
            "FROZEN_HASH_MISSING",
        ),
    ],
)
def test_health_fails_for_material_fixture_contract_mutations(tmp_path: Path, mutation, expected_code: str) -> None:
    fixture = build_replay_decision_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).fillna("")
    mutation(rows).to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_replay_decision_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("row_id", "column", "value", "expected_code"),
    [
        (
            "SYNTH_BLOCKED_FUTURE_AVAILABLE_EVIDENCE_DECISION",
            "decision_time_eligible",
            "True",
            "FUTURE_AVAILABLE_EVIDENCE_NOT_BLOCKED",
        ),
        (
            "SYNTH_REVIEW_BUY_CANDIDATE_REPORT_ONLY_DECISION",
            "trade_usage",
            "buy_signal",
            "REVIEW_CANDIDATE_TREATED_AS_ORDER_SIGNAL",
        ),
        (
            "SYNTH_REVIEW_SELL_CANDIDATE_REPORT_ONLY_DECISION",
            "trading_allowed",
            "True",
            "REVIEW_CANDIDATE_TREATED_AS_ORDER_SIGNAL",
        ),
        (
            "SYNTH_BLOCKED_RISK_VETO_ST_DELIST_DECISION",
            "decision_actionability",
            "review_only",
            "RISK_VETO_ROW_DOES_NOT_BLOCK_ACTIONABILITY",
        ),
        (
            "SYNTH_BLOCKED_MISSING_REPLAY_EVIDENCE_BUNDLE_DECISION",
            "decision_time_eligible",
            "True",
            "MISSING_BUNDLE_ROW_NOT_BLOCKED",
        ),
        (
            "SYNTH_BLOCKED_RESTRICTED_OR_PRIVATE_SOURCE_DECISION",
            "trade_usage",
            "review_only",
            "RESTRICTED_PRIVATE_ROW_NOT_BLOCKED",
        ),
        (
            "SYNTH_OBSERVE_ONLY_INCOMPLETE_REVIEW_DECISION",
            "decision_time_eligible",
            "True",
            "OBSERVE_ONLY_INCOMPLETE_DECISION_ELIGIBLE",
        ),
    ],
)
def test_health_fails_for_special_row_contract_mutations(
    tmp_path: Path, row_id: str, column: str, value: str, expected_code: str
) -> None:
    fixture = build_replay_decision_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).fillna("")
    rows.loc[rows["replay_decision_id"] == row_id, column] = value
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_replay_decision_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("column", "value", "expected_code"),
    [
        ("forward_labels_created", "True", "FORWARD_LABELS_CREATED_TRUE"),
        ("future_labels_joined", "True", "FUTURE_LABELS_JOINED_TRUE"),
        ("signal_score_implemented", "True", "SIGNAL_SCORE_FLAG_TRUE"),
        ("signal_score_input_authorized", "True", "SIGNAL_SCORE_FLAG_TRUE"),
        ("model_training_allowed", "True", "MODEL_TRAINING_FLAG_TRUE"),
        ("active_weight_allowed", "True", "ACTIVE_WEIGHT_THRESHOLD_FLAG_TRUE"),
        ("active_threshold_allowed", "True", "ACTIVE_WEIGHT_THRESHOLD_FLAG_TRUE"),
        ("stock_profile_validation_allowed", "True", "STOCK_PROFILE_FLAG_TRUE"),
        ("paper_validation_allowed", "True", "PAPER_VALIDATION_FLAG_TRUE"),
        ("real_buy_review_allowed", "True", "BUY_REVIEW_FLAG_TRUE"),
        ("buy_review_allowed", "True", "BUY_REVIEW_FLAG_TRUE"),
        ("strategy_performance_validated", "True", "PERFORMANCE_OR_TRADING_FLAG_TRUE"),
        ("trading_allowed", "True", "PERFORMANCE_OR_TRADING_FLAG_TRUE"),
        ("trade_usage", "active_model_input", "TRADE_USAGE_FORBIDDEN"),
        ("decision_rationale_summary", "contains access_token test", "SENSITIVE_TEXT_DETECTED"),
        ("real_replay_decisions_created", "True", "REAL_REPLAY_DECISION_FLAG_TRUE"),
        ("real_replay_evidence_bundle_used", "True", "REAL_REPLAY_EVIDENCE_BUNDLE_USED_TRUE"),
        ("broker_api_called", "True", "BROKER_API_LLM_FLAG_TRUE"),
        ("external_api_called", "True", "BROKER_API_LLM_FLAG_TRUE"),
        ("llm_api_called", "True", "BROKER_API_LLM_FLAG_TRUE"),
        ("data_raw_written", "True", "DATA_WRITE_FLAG_TRUE"),
        ("data_processed_written", "True", "DATA_WRITE_FLAG_TRUE"),
        ("data_cache_written", "True", "DATA_WRITE_FLAG_TRUE"),
        ("current_candidates_run", "True", "OPERATIONAL_SIDE_EFFECT_FLAG_TRUE"),
        ("snapshot_built", "True", "OPERATIONAL_SIDE_EFFECT_FLAG_TRUE"),
        ("signal_semantics_changed", "True", "OPERATIONAL_SIDE_EFFECT_FLAG_TRUE"),
        ("active_stock_profile_created", "True", "OPERATIONAL_SIDE_EFFECT_FLAG_TRUE"),
    ],
)
def test_health_fails_for_forbidden_output_and_side_effect_flags(
    tmp_path: Path, column: str, value: str, expected_code: str
) -> None:
    fixture = build_replay_decision_schema_fixture(output_dir=tmp_path)
    rows = pd.read_csv(fixture.artifact_paths["fixture_rows"], dtype=str).fillna("")
    rows.loc[0, column] = value
    rows.to_csv(fixture.artifact_paths["fixture_rows"], index=False)

    result = check_replay_decision_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


@pytest.mark.parametrize(
    ("flag", "expected_code"),
    [(flag, "FORBIDDEN_METADATA_FLAG_TRUE") for flag in FORBIDDEN_METADATA_FALSE_FLAGS],
)
def test_health_fails_for_forbidden_metadata_flags(tmp_path: Path, flag: str, expected_code: str) -> None:
    fixture = build_replay_decision_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata[flag] = True
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_replay_decision_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert expected_code in _issue_codes(result)


def test_health_fails_for_unsafe_artifact_path_in_metadata(tmp_path: Path) -> None:
    fixture = build_replay_decision_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["artifact_paths"] = {"bad": "data/raw/replay_decision.csv"}
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    result = check_replay_decision_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert "UNSAFE_ARTIFACT_PATH" in _issue_codes(result)


def test_status_safe_empty_and_latest_fixture_summary(tmp_path: Path) -> None:
    empty = run_replay_decision_schema_fixture_status(root=tmp_path / "missing", output_dir=tmp_path / "status_empty")

    assert empty.status == "PASS"
    assert empty.workflow_stage == NO_REPLAY_DECISION_SCHEMA_FIXTURE
    assert empty.health_status == "PASS"
    assert empty.latest_run_id == ""
    assert empty.report_only is True
    assert empty.diagnostic_only is True
    assert empty.artifact_paths["status_csv"].exists()

    fixture = build_replay_decision_schema_fixture(output_dir=tmp_path)
    status = run_replay_decision_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert status.latest_run_id == fixture.replay_decision_schema_fixture_id
    assert status.status == "PASS"
    assert status.workflow_stage == REPLAY_DECISION_SCHEMA_FIXTURE_CREATED
    assert status.health_status == "PASS"
    assert status.decision_count == 10
    assert status.validation_issue_count == 0
    assert status.report_only is True
    assert status.diagnostic_only is True
    assert status.replay_decision_schema_fixture_created is True
    assert status.replay_decision_rows_created is True
    assert status.replay_evidence_bundle_schema_fixture_used is True
    assert status.real_replay_decisions_created is False
    assert status.real_replay_evidence_bundle_used is False
    assert status.forward_labels_created is False
    assert status.future_labels_joined is False
    assert status.signal_score_input_authorized is False
    assert status.buy_review_allowed is False
    assert status.trading_allowed is False
    assert "core/views/research-status/checkpoint context is available" in status.next_action
    assert "post-checkpoint governance audit" in status.next_action
    assert "research-status/checkpoint integration only after the views remain stable" not in status.next_action
    assert "forward label readiness" not in status.next_action.lower()


def test_status_reports_invalid_when_health_fails(tmp_path: Path) -> None:
    fixture = build_replay_decision_schema_fixture(output_dir=tmp_path)
    metadata = _metadata(fixture.artifact_paths["metadata"])
    metadata["status"] = "MAYBE"
    fixture.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    status = run_replay_decision_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert status.status == "FAIL"
    assert status.workflow_stage == REPLAY_DECISION_SCHEMA_FIXTURE_INVALID
    assert status.health_status == "FAIL"


def test_cli_index_health_status_commands_run_successfully(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "replay_decision_schema_fixture_v0_1"
    build = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "replay-decision-schema-fixture",
            "--output-dir",
            str(root),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    assert "status: PASS" in build.stdout

    for command in [
        "replay-decision-schema-fixture-index",
        "replay-decision-schema-fixture-health",
        "replay-decision-schema-fixture-status",
    ]:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "quant_replay_system.cli",
                command,
                "--root",
                str(root),
                "--output-dir",
                str(root / command.rsplit("-", 1)[-1]),
            ],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
        )
        assert "real replay decisions" in completed.stdout.lower()
        assert "trading" in completed.stdout.lower()

    assert not (tmp_path / "docs" / "project_sources").exists()


def _metadata(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _issue_codes(result) -> set[str]:
    if result.health_frame.empty:
        return set()
    return set(result.health_frame["issue_code"].astype(str))
