from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system.reviewed_local_csv_replay_prototype_input_contract_fixture import (
    CONTRACT_FILE_NAMES,
    REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED,
    SAFETY_FALSE_FLAGS,
    build_reviewed_local_csv_replay_prototype_input_contract_fixture,
)


EXPECTED_ARTIFACTS = {
    "metadata.json",
    "reviewed_local_csv_replay_prototype_input_contract_fixture_report.md",
    "reviewed_local_csv_contract_matrix.csv",
    "reviewed_local_csv_field_contract.csv",
    "reviewed_local_csv_pit_rule_matrix.csv",
    "reviewed_local_csv_lineage_rule_matrix.csv",
    "reviewed_local_csv_quality_review_rule_matrix.csv",
    "reviewed_local_csv_forbidden_interpretation_matrix.csv",
    "reviewed_local_csv_safety_flags.json",
    "recommended_next_task.md",
}


def _build(tmp_path: Path):
    return build_reviewed_local_csv_replay_prototype_input_contract_fixture(
        output_dir=tmp_path
        / "outputs"
        / "reports"
        / "manual_diagnostics"
        / "reviewed_local_csv_replay_prototype_input_contract_fixture_v0_1"
    )


def _metadata(result) -> dict:
    return json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))


def _csv(result, key: str) -> pd.DataFrame:
    return pd.read_csv(result.artifact_paths[key], dtype=str).fillna("")


def test_reviewed_local_csv_contract_fixture_writes_required_artifacts(tmp_path: Path) -> None:
    result = _build(tmp_path)

    assert result.status == "PASS"
    assert result.workflow_stage == REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED
    assert result.status != REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED
    assert result.contract_count == 12
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_paths["artifact_dir"].is_relative_to(
        tmp_path
        / "outputs"
        / "reports"
        / "manual_diagnostics"
        / "reviewed_local_csv_replay_prototype_input_contract_fixture_v0_1"
    )
    assert {path.name for path in result.artifact_paths["artifact_dir"].iterdir()} == EXPECTED_ARTIFACTS
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()


def test_metadata_status_stage_and_safety_flags_are_safe(tmp_path: Path) -> None:
    metadata = _metadata(_build(tmp_path))

    assert metadata["workflow_name"] == "reviewed_local_csv_replay_prototype_input_contract_fixture"
    assert metadata["status"] == "PASS"
    assert metadata["workflow_stage"] == REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED
    assert metadata["status"] != REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED
    assert metadata["contract_count"] == 12
    assert metadata["validation_issue_count"] == 0
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert metadata["schema_fixture"] is True
    for flag in SAFETY_FALSE_FLAGS:
        assert metadata[flag] is False


def test_contract_matrix_has_all_12_groups_and_key_semantics(tmp_path: Path) -> None:
    result = _build(tmp_path)
    contracts = _csv(result, "contract_matrix").set_index("file_name")

    assert set(contracts.index) == set(CONTRACT_FILE_NAMES)
    assert len(contracts) == 12

    forward_label = contracts.loc["forward_return_label_reviewed.csv"]
    assert forward_label["current_allowed_status"] == "FUTURE_ONLY_BLOCKED_AS_DECISION_TIME_INPUT"
    assert "blocked as decision-time input" in forward_label["forbidden_interpretation"]
    assert "Frozen replay decision" in forward_label["future_gate_required"]

    benchmark = contracts.loc["benchmark_data_reviewed.csv"]
    assert benchmark["current_allowed_status"] == "OPTIONAL_REPORT_ONLY_CONTEXT"
    assert "not benchmark outperformance proof" in benchmark["forbidden_interpretation"]

    market_data = contracts.loc["market_data_reviewed.csv"]
    market_forbidden = market_data["forbidden_interpretation"].lower()
    assert "not market-cache mutation" in market_forbidden
    assert "not current-candidates input" in market_forbidden

    replay_decision = contracts.loc["replay_decision_reviewed.csv"]
    assert "not decision freeze" in replay_decision["forbidden_interpretation"]

    source_registry = contracts.loc["source_registry_reviewed.csv"]
    assert "not live fetch authorization" in source_registry["forbidden_interpretation"]


def test_field_contract_tracks_required_pit_lineage_quality_and_reviewer_fields(tmp_path: Path) -> None:
    result = _build(tmp_path)
    fields = _csv(result, "field_contract")

    assert {"source_hash", "revision_id", "available_time", "reviewer_id", "reviewed_at", "review_status"}.issubset(
        set(fields["field_name"])
    )
    assert set(fields.loc[fields["field_name"] == "available_time", "pit_role"]) == {"PIT_FIELD"}
    assert "SOURCE_LINEAGE_FIELD" in set(fields.loc[fields["field_name"] == "source_hash", "source_lineage_role"])
    assert "SOURCE_LINEAGE_FIELD" in set(fields.loc[fields["field_name"] == "revision_id", "source_lineage_role"])
    assert "QUALITY_FIELD" in set(fields.loc[fields["field_name"] == "quality_status", "quality_role"])
    assert "REVIEWER_FIELD" in set(fields.loc[fields["field_name"] == "reviewer_id", "reviewer_role"])
    assert "forward_return_label_reviewed.csv" in set(fields["file_name"])
    assert "label_window_start" in set(fields.loc[fields["file_name"] == "forward_return_label_reviewed.csv", "field_name"])


def test_pit_lineage_quality_and_forbidden_rule_matrices_are_present(tmp_path: Path) -> None:
    result = _build(tmp_path)
    pit_rules = _csv(result, "pit_rule_matrix")
    lineage = _csv(result, "lineage_rule_matrix")
    quality = _csv(result, "quality_review_rule_matrix")
    forbidden = _csv(result, "forbidden_interpretation_matrix")

    assert {
        "available_time_cutoff",
        "event_date_not_available_time",
        "period_end_not_available_time",
        "publish_time_not_available_time",
        "fetched_at_not_available_time",
        "reviewed_at_audit_only",
        "future_prices_excluded",
        "future_labels_excluded",
        "source_hash_required",
        "revision_id_required",
        "permission_gate_required",
        "quality_gate_required",
        "reviewer_approval_no_pit_override",
    }.issubset(set(pit_rules["rule_id"]))
    assert (pit_rules["required_for_future_pit_admissibility"] == "True").all()
    assert "source_hash" in set(lineage["lineage_rule"])
    assert "review_status" in set(quality["quality_review_rule"])
    assert len(forbidden) == 12


def test_safety_flags_report_and_next_task_are_bounded(tmp_path: Path) -> None:
    result = _build(tmp_path)
    safety = json.loads(result.artifact_paths["safety_flags"].read_text(encoding="utf-8"))
    report = result.artifact_paths["report"].read_text(encoding="utf-8")
    next_task = result.artifact_paths["recommended_next_task"].read_text(encoding="utf-8")
    all_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in result.artifact_paths["artifact_dir"].iterdir()
        if path.suffix in {".json", ".csv", ".md"}
    )

    for flag in SAFETY_FALSE_FLAGS:
        assert safety[flag] is False
    assert "No real reviewed input package is created" in report
    assert "No PIT admissibility validator is implemented" in report
    assert "No future labels are joined to decision inputs" in report
    assert "Reviewed LOCAL_CSV Replay Prototype Input Contract Fixture Views Report-Only v0.1" in next_task
    assert not re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", all_text.lower())


def test_cli_command_runs_and_view_commands_are_registered(tmp_path: Path) -> None:
    output_dir = (
        tmp_path
        / "outputs"
        / "reports"
        / "manual_diagnostics"
        / "reviewed_local_csv_replay_prototype_input_contract_fixture_v0_1"
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "reviewed-local-csv-replay-prototype-input-contract-fixture",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "reviewed_local_csv_replay_prototype_input_contract_fixture_id:" in completed.stdout
    assert "status: PASS" in completed.stdout
    assert f"workflow_stage: {REVIEWED_LOCAL_CSV_REPLAY_PROTOTYPE_INPUT_CONTRACT_FIXTURE_CREATED}" in completed.stdout
    assert "contract_count: 12" in completed.stdout
    assert "validation_issue_count: 0" in completed.stdout
    assert "report_only: True" in completed.stdout
    assert "diagnostic_only: True" in completed.stdout
    assert "No real reviewed input package" in completed.stdout

    artifact_dirs = [path for path in output_dir.iterdir() if path.is_dir()]
    assert len(artifact_dirs) == 1
    assert (artifact_dirs[0] / "reviewed_local_csv_contract_matrix.csv").exists()

    help_output = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout
    assert "reviewed-local-csv-replay-prototype-input-contract-fixture" in help_output
    assert "reviewed-local-csv-replay-prototype-input-contract-fixture-index" in help_output
    assert "reviewed-local-csv-replay-prototype-input-contract-fixture-health" in help_output
    assert "reviewed-local-csv-replay-prototype-input-contract-fixture-status" in help_output
