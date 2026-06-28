from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system.forward_return_label_schema_fixture import (
    FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED,
    FORBIDDEN_METADATA_FALSE_FLAGS,
    REQUIRED_FORWARD_RETURN_LABEL_FIELDS,
    ROW_FALSE_FLAGS,
    build_forward_return_label_schema_fixture,
)


EXPECTED_ARTIFACTS = {
    "metadata.json",
    "forward_return_label_schema_fixture_report.md",
    "forward_return_label_schema_fixture.csv",
    "forward_return_label_case_matrix.csv",
    "forward_return_label_field_contract.csv",
    "forward_return_label_validation_results.csv",
    "forward_return_label_leakage_guard_results.csv",
    "forward_return_label_safety_flags.json",
    "recommended_next_task.md",
}

REQUIRED_CASES = {
    "SYNTH_FWD_1D_COMPLETE_LABEL",
    "SYNTH_FWD_5D_COMPLETE_LABEL",
    "SYNTH_FWD_20D_COMPLETE_BENCHMARK_RELATIVE_LABEL",
    "SYNTH_NEGATIVE_FORWARD_RETURN_LABEL",
    "SYNTH_POSITIVE_FORWARD_RETURN_LABEL",
    "SYNTH_BLOCKED_NOT_FROZEN_DECISION_LABEL",
    "SYNTH_BLOCKED_MISSING_EXIT_PRICE_LABEL",
    "SYNTH_BLOCKED_INVALID_WINDOW_LABEL",
    "SYNTH_EXECUTION_BLOCKED_SUSPENSION_LABEL",
    "SYNTH_PARTIAL_BENCHMARK_OR_INDUSTRY_LABEL",
}


def _build(tmp_path: Path):
    return build_forward_return_label_schema_fixture(
        output_dir=tmp_path
        / "outputs"
        / "reports"
        / "manual_diagnostics"
        / "forward_return_label_schema_fixture_v0_1"
    )


def _rows(result) -> pd.DataFrame:
    return pd.read_csv(result.artifact_paths["fixture_rows"], dtype=str).fillna("")


def _metadata(result) -> dict:
    return json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))


def test_forward_return_label_schema_fixture_writes_required_artifacts(tmp_path: Path) -> None:
    result = _build(tmp_path)

    assert result.status == "PASS"
    assert result.workflow_stage == FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED
    assert result.status != FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED
    assert result.label_count == 10
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_paths["artifact_dir"].is_relative_to(
        tmp_path / "outputs" / "reports" / "manual_diagnostics" / "forward_return_label_schema_fixture_v0_1"
    )
    assert {path.name for path in result.artifact_paths["artifact_dir"].iterdir()} == EXPECTED_ARTIFACTS
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()


def test_metadata_status_stage_and_forbidden_flags_are_safe(tmp_path: Path) -> None:
    metadata = _metadata(_build(tmp_path))

    assert metadata["workflow_name"] == "forward_return_label_schema_fixture"
    assert metadata["status"] == "PASS"
    assert metadata["workflow_stage"] == FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED
    assert metadata["status"] != FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED
    assert metadata["label_count"] == 10
    assert metadata["validation_issue_count"] == 0
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert metadata["schema_fixture"] is True
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert metadata[flag] is False


def test_rows_include_required_fields_unique_cases_and_leading_zero_symbol(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result)
    fields = pd.read_csv(result.artifact_paths["field_contract"], dtype=str).fillna("")

    assert len(rows) == 10
    assert set(REQUIRED_FORWARD_RETURN_LABEL_FIELDS).issubset(set(rows.columns))
    assert set(REQUIRED_FORWARD_RETURN_LABEL_FIELDS).issubset(set(fields["field_name"]))
    assert set(rows["schema_fixture_case_id"]) == REQUIRED_CASES
    assert rows["forward_return_label_id"].is_unique
    assert rows.loc[rows["schema_fixture_case_id"] == "SYNTH_FWD_1D_COMPLETE_LABEL", "symbol"].iloc[0] == "000001"
    assert rows["symbol"].map(type).eq(str).all()
    assert (rows["source_replay_decision_fixture_id"] == "356bbd57a4d6").all()
    assert (rows["replay_decision_workflow_stage"] == "REPLAY_DECISION_SCHEMA_FIXTURE_CREATED").all()
    assert (rows["replay_decision_health_status"] == "PASS").all()


def test_complete_labels_have_valid_windows_and_safe_interpretation(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path))
    complete = rows[rows["label_status"] == "COMPLETE"]

    assert not complete.empty
    assert set(complete["schema_fixture_case_id"]) == {
        "SYNTH_FWD_1D_COMPLETE_LABEL",
        "SYNTH_FWD_5D_COMPLETE_LABEL",
        "SYNTH_FWD_20D_COMPLETE_BENCHMARK_RELATIVE_LABEL",
        "SYNTH_NEGATIVE_FORWARD_RETURN_LABEL",
        "SYNTH_POSITIVE_FORWARD_RETURN_LABEL",
    }
    assert complete.apply(
        lambda row: pd.Timestamp(row["window_start_date"]) > pd.Timestamp(row["replay_decision_time"]),
        axis=1,
    ).all()
    assert complete.apply(
        lambda row: pd.Timestamp(row["window_end_date"]) > pd.Timestamp(row["window_start_date"]),
        axis=1,
    ).all()
    assert complete["entry_price"].astype(str).str.len().gt(0).all()
    assert complete["exit_price"].astype(str).str.len().gt(0).all()
    assert (complete["window_valid"] == "True").all()
    assert (complete["tradeable_at_entry"] == "True").all()
    assert (complete["tradeable_at_exit"] == "True").all()
    assert (complete["real_forward_label_created"] == "False").all()


def test_required_blocked_and_partial_cases_have_expected_reasons(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path)).set_index("schema_fixture_case_id")

    not_frozen = rows.loc["SYNTH_BLOCKED_NOT_FROZEN_DECISION_LABEL"]
    assert not_frozen["label_status"] == "BLOCKED"
    assert not_frozen["replay_decision_frozen"] == "False"
    assert "not frozen" in not_frozen["blocker_reason"].lower()
    assert not_frozen["real_forward_label_created"] == "False"

    missing_exit = rows.loc["SYNTH_BLOCKED_MISSING_EXIT_PRICE_LABEL"]
    assert missing_exit["label_status"] == "BLOCKED"
    assert missing_exit["exit_price"] == ""
    assert missing_exit["label_completeness_status"] == "MISSING_EXIT_PRICE"
    assert missing_exit["execution_blocker_type"] == "MISSING_PRICE"

    invalid_window = rows.loc["SYNTH_BLOCKED_INVALID_WINDOW_LABEL"]
    assert invalid_window["label_status"] == "BLOCKED"
    assert invalid_window["window_valid"] == "False"
    assert invalid_window["label_completeness_status"] == "INVALID_WINDOW"
    assert pd.Timestamp(invalid_window["window_start_date"]) <= pd.Timestamp(invalid_window["replay_decision_time"])

    suspension = rows.loc["SYNTH_EXECUTION_BLOCKED_SUSPENSION_LABEL"]
    assert suspension["label_status"] in {"BLOCKED", "PARTIAL"}
    assert suspension["execution_blocker_type"] == "SUSPENSION"
    assert suspension["suspended_during_window"] == "True"

    partial = rows.loc["SYNTH_PARTIAL_BENCHMARK_OR_INDUSTRY_LABEL"]
    assert partial["label_status"] == "PARTIAL"
    assert partial["relative_label_available"] == "False"
    assert partial["partial_label_reason"]


def test_return_direction_and_relative_label_cases(tmp_path: Path) -> None:
    rows = _rows(_build(tmp_path)).set_index("schema_fixture_case_id")

    negative = rows.loc["SYNTH_NEGATIVE_FORWARD_RETURN_LABEL"]
    assert negative["return_direction"] == "NEGATIVE"
    assert negative["return_bucket"] == "LOSS"
    assert float(negative["forward_return_pct"]) < 0
    assert negative["buy_review_allowed"] == "False"

    positive = rows.loc["SYNTH_POSITIVE_FORWARD_RETURN_LABEL"]
    assert positive["return_direction"] == "POSITIVE"
    assert positive["return_bucket"] == "GAIN"
    assert float(positive["forward_return_pct"]) > 0
    assert positive["real_buy_review_allowed"] == "False"

    relative = rows.loc["SYNTH_FWD_20D_COMPLETE_BENCHMARK_RELATIVE_LABEL"]
    for column in [
        "benchmark_entry_price",
        "benchmark_exit_price",
        "benchmark_forward_return",
        "benchmark_relative_return",
        "industry_forward_return",
        "industry_relative_return",
    ]:
        assert relative[column] != ""
    assert relative["relative_label_available"] == "True"


def test_row_and_metadata_safety_flags_and_leakage_guards(tmp_path: Path) -> None:
    result = _build(tmp_path)
    rows = _rows(result)
    metadata = _metadata(result)
    leakage = pd.read_csv(result.artifact_paths["leakage_guard_results"], dtype=str).fillna("")
    safety = json.loads(result.artifact_paths["safety_flags"].read_text(encoding="utf-8"))

    for flag in ROW_FALSE_FLAGS:
        assert (rows[flag] == "False").all(), flag
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        assert metadata[flag] is False
        assert safety[flag] is False
    assert (leakage["passed"] == "True").all()
    assert not leakage["guard_name"].str.contains("active_model_input|current_candidate_input|trading_signal").any()


def test_validation_results_report_and_recommended_next_task_are_safe(tmp_path: Path) -> None:
    result = _build(tmp_path)
    validation = pd.read_csv(result.artifact_paths["validation_results"], dtype=str).fillna("")
    case_matrix = pd.read_csv(result.artifact_paths["case_matrix"], dtype=str).fillna("")
    report = result.artifact_paths["report"].read_text(encoding="utf-8")
    next_task = result.artifact_paths["recommended_next_task"].read_text(encoding="utf-8")
    all_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in result.artifact_paths["artifact_dir"].iterdir()
        if path.suffix in {".json", ".csv", ".md"}
    )

    assert (validation["passed"] == "True").all()
    assert len(case_matrix) == 10
    assert "No real forward labels" in report
    assert "No future labels joined" in report
    assert "No model training" in report
    assert "No buy-review" in report
    assert "No trading" in report
    assert "Forward Return Label Schema Fixture Views Report-Only v0.1" in next_task
    assert not re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", all_text.lower())


def test_cli_command_runs_and_view_commands_are_registered(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "forward_return_label_schema_fixture_v0_1"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "forward-return-label-schema-fixture",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "forward_return_label_schema_fixture_id:" in completed.stdout
    assert "status: PASS" in completed.stdout
    assert f"workflow_stage: {FORWARD_RETURN_LABEL_SCHEMA_FIXTURE_CREATED}" in completed.stdout
    assert "label_count: 10" in completed.stdout
    assert "validation_issue_count: 0" in completed.stdout
    assert "report_only: True" in completed.stdout
    assert "diagnostic_only: True" in completed.stdout
    assert "No real forward labels" in completed.stdout

    artifact_dirs = [path for path in output_dir.iterdir() if path.is_dir()]
    assert len(artifact_dirs) == 1
    assert (artifact_dirs[0] / "forward_return_label_schema_fixture.csv").exists()

    help_output = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout
    assert "forward-return-label-schema-fixture" in help_output
    assert "forward-return-label-schema-fixture-index" in help_output
    assert "forward-return-label-schema-fixture-health" in help_output
    assert "forward-return-label-schema-fixture-status" in help_output
