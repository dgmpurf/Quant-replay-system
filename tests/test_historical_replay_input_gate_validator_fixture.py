from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system.historical_replay_input_gate_validator_fixture import (
    EXPECTED_FIXTURE_CASE_GROUP_COUNTS,
    build_historical_replay_input_gate_validator_fixture,
)


def test_fixture_workflow_writes_required_report_only_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "historical_replay_input_gate_validator_fixture_v0_1"

    result = build_historical_replay_input_gate_validator_fixture(output_dir=output_dir)

    assert result.status == "PASS"
    assert result.case_count == 68
    assert result.blocked_case_count == 67
    assert result.pass_candidate_case_count == 1
    assert result.active_ready_case_count == 0
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.active_replay_input is False
    assert result.forward_labels_exist is False
    assert result.weights_trained is False
    assert result.active_stock_profile_exists is False
    assert result.real_buy_review_eligible is False

    artifact_dir = result.artifact_paths["artifact_dir"]
    assert artifact_dir.is_relative_to(output_dir)
    for key in [
        "metadata",
        "fixture_cases",
        "blocked_requirements",
        "expected_status_matrix",
        "fixture_input_schema",
        "overclaim_guard_report",
        "report",
        "recommended_next_task",
    ]:
        assert result.artifact_paths[key].exists()

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["fixture_run_id"] == result.fixture_run_id
    assert metadata["case_count"] == 68
    assert metadata["blocked_case_count"] == 67
    assert metadata["pass_candidate_case_count"] == 1
    assert metadata["active_ready_case_count"] == 0
    assert metadata["active_replay_input"] is False
    assert metadata["forward_labels_exist"] is False
    assert metadata["weights_trained"] is False
    assert metadata["active_stock_profile_exists"] is False
    assert metadata["real_buy_review_eligible"] is False
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert metadata["no_live_trading"] is True
    assert metadata["no_broker_api"] is True
    assert metadata["no_order_placement"] is True
    assert metadata["no_message_sent"] is True
    assert metadata["llm_api_called"] is False
    assert metadata["external_api_called"] is False
    assert metadata["cache_mutated"] is False
    assert metadata["current_candidates_run"] is False
    assert metadata["snapshot_built"] is False
    assert metadata["signal_semantics_changed"] is False
    assert metadata["validator_implemented"] is False
    assert metadata["active_ready_status_allowed"] is False


def test_fixture_case_counts_statuses_and_downstream_blocks(tmp_path: Path) -> None:
    result = build_historical_replay_input_gate_validator_fixture(output_dir=tmp_path)

    cases = pd.read_csv(result.artifact_paths["fixture_cases"], dtype=str)
    status = pd.read_csv(result.artifact_paths["expected_status_matrix"], dtype=str)

    assert len(cases) == 68
    assert cases.groupby("case_group").size().to_dict() == EXPECTED_FIXTURE_CASE_GROUP_COUNTS
    assert (cases["active_allowed"] == "False").all()
    assert "ACTIVE_REPLAY_INPUT_READY" not in set(cases["expected_status"])
    assert (cases["expected_status"] == "REPLAY_INPUT_GATE_PASS_CANDIDATE").sum() == 1
    assert (cases["case_group"] == "ACTIVE_READY_BOUNDARY").sum() == 1
    assert cases.loc[cases["case_group"] == "ACTIVE_READY_BOUNDARY", "expected_status"].iloc[0] == "NO_INPUT"

    for column in [
        "should_block_replay",
        "should_block_forward_labels",
        "should_block_training",
        "should_block_stock_profile",
        "should_block_buy_review",
    ]:
        assert (status[column] == "True").all()


def test_fixture_input_schema_preserves_leading_zero_symbol_and_overclaim_guards_pass(tmp_path: Path) -> None:
    result = build_historical_replay_input_gate_validator_fixture(output_dir=tmp_path)

    schema = pd.read_csv(result.artifact_paths["fixture_input_schema"], dtype=str)
    guards = pd.read_csv(result.artifact_paths["overclaim_guard_report"], dtype=str)

    symbol_rows = schema[(schema["field_group"] == "pit_universe") & (schema["field_name"] == "symbol")]
    assert not symbol_rows.empty
    assert "Preserve leading zeros" in symbol_rows.iloc[0]["notes"]

    assert len(guards) >= 10
    assert (guards["passed"] == "True").all()
    assert result.overclaim_guard_pass_count == result.overclaim_guard_total_count


def test_fixture_workflow_does_not_write_data_paths(tmp_path: Path) -> None:
    build_historical_replay_input_gate_validator_fixture(output_dir=tmp_path / "outputs" / "reports" / "manual_diagnostics")

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_fixture_cli_runs_and_prints_summary(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "historical_replay_input_gate_validator_fixture_v0_1"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "historical-replay-input-gate-validator-fixture",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "fixture_run_id:" in completed.stdout
    assert "case_count: 68" in completed.stdout
    assert "pass_candidate_case_count: 1" in completed.stdout
    assert "active_ready_case_count: 0" in completed.stdout
    assert "validator_implemented: False" in completed.stdout
    assert "No replay, current-candidates" in completed.stdout
    assert len([path for path in output_dir.iterdir() if path.is_dir()]) == 1
