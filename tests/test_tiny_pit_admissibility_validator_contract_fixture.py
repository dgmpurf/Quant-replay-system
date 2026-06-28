from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system.tiny_pit_admissibility_validator_contract_fixture import (
    REQUIRED_GATE_GROUPS,
    REQUIRED_PACKAGE_SECTIONS,
    SAFETY_FALSE_FLAGS,
    TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED,
    build_tiny_pit_admissibility_validator_contract_fixture,
)


EXPECTED_ARTIFACTS = {
    "metadata.json",
    "tiny_pit_admissibility_validator_contract_fixture_report.md",
    "gate_case_matrix.csv",
    "package_section_contract.csv",
    "output_status_contract.csv",
    "pit_timing_rule_matrix.csv",
    "forbidden_interpretation_matrix.csv",
    "safety_flags.json",
    "limitations.md",
    "recommended_next_task.md",
}

EXPECTED_CASES = {
    "NO_INPUT",
    "PACKAGE_READ_FAILED",
    "PACKAGE_SCHEMA_INVALID",
    "PACKAGE_PIT_BLOCKED_AVAILABLE_TIME",
    "PACKAGE_PIT_BLOCKED_MISSING_SOURCE_HASH",
    "PACKAGE_PIT_BLOCKED_MISSING_REVISION_ID",
    "PACKAGE_PIT_BLOCKED_REVIEW_STATUS",
    "PACKAGE_PIT_BLOCKED_SOURCE_PERMISSION",
    "PACKAGE_PIT_BLOCKED_QUALITY_STATUS",
    "PACKAGE_PIT_BLOCKED_FORWARD_LABEL_LEAKAGE",
    "PACKAGE_REVIEW_REQUIRED",
    "PIT_ADMISSIBILITY_PASS_CANDIDATE",
}

FORBIDDEN_FUTURE_STATUSES = {
    "ACTIVE_REPLAY_INPUT_READY",
    "REAL_REPLAY_READY",
    "FORWARD_LABEL_READY",
    "TRAINING_READY",
    "STOCK_PROFILE_READY",
    "BUY_REVIEW_READY",
}

EXPECTED_TIMING_RULES = {
    "replay_decision_time_central_cutoff",
    "available_time_lte_replay_decision_time",
    "event_date_not_available_time",
    "period_end_not_available_time",
    "publish_time_not_always_available_time",
    "fetched_at_after_replay_requires_historical_availability",
    "reviewed_at_audit_metadata_only",
    "reviewer_approval_no_pit_override",
    "future_forward_labels_excluded_from_decision_inputs",
    "future_labels_not_joined_to_decision_or_training",
}


def _build(tmp_path: Path):
    return build_tiny_pit_admissibility_validator_contract_fixture(
        output_dir=tmp_path
        / "outputs"
        / "reports"
        / "manual_diagnostics"
        / "tiny_pit_admissibility_validator_contract_fixture_v0_1"
    )


def _metadata(result) -> dict:
    return json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))


def _csv(result, key: str) -> pd.DataFrame:
    return pd.read_csv(result.artifact_paths[key], dtype=str).fillna("")


def _split_semicolon(values: pd.Series) -> set[str]:
    observed: set[str] = set()
    for value in values:
        observed.update(part.strip() for part in str(value).split(";") if part.strip())
    return observed


def test_tiny_pit_contract_fixture_writes_required_artifacts(tmp_path: Path) -> None:
    result = _build(tmp_path)

    assert result.status == "PASS"
    assert result.workflow_stage == TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED
    assert result.status != TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED
    assert result.case_count == 12
    assert result.package_section_count == 12
    assert result.gate_group_count == len(REQUIRED_GATE_GROUPS)
    assert result.validation_issue_count == 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_paths["artifact_dir"].is_relative_to(
        tmp_path
        / "outputs"
        / "reports"
        / "manual_diagnostics"
        / "tiny_pit_admissibility_validator_contract_fixture_v0_1"
    )
    assert {path.name for path in result.artifact_paths["artifact_dir"].iterdir()} == EXPECTED_ARTIFACTS
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_metadata_status_stage_and_safety_flags_are_safe(tmp_path: Path) -> None:
    metadata = _metadata(_build(tmp_path))

    assert metadata["workflow_name"] == "tiny_pit_admissibility_validator_contract_fixture"
    assert metadata["status"] == "PASS"
    assert metadata["workflow_stage"] == TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED
    assert metadata["status"] != TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED
    assert metadata["case_count"] == 12
    assert metadata["package_section_count"] == 12
    assert metadata["gate_group_count"] == len(REQUIRED_GATE_GROUPS)
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert metadata["contract_fixture"] is True
    assert metadata["recommended_next_task"] == "Tiny PIT Admissibility Validator Contract Fixture Views Report-Only v0.1"
    for flag in SAFETY_FALSE_FLAGS:
        assert metadata[flag] is False


def test_gate_cases_sections_statuses_and_timing_rules_are_complete(tmp_path: Path) -> None:
    result = _build(tmp_path)
    cases = _csv(result, "gate_case_matrix")
    sections = _csv(result, "package_section_contract")
    statuses = _csv(result, "output_status_contract")
    timing_rules = _csv(result, "pit_timing_rule_matrix")

    assert set(cases["case_name"]) == EXPECTED_CASES
    assert _split_semicolon(cases["gate_groups"]) == set(REQUIRED_GATE_GROUPS)
    assert set(sections["section_name"]) == set(REQUIRED_PACKAGE_SECTIONS)
    assert set(timing_rules["timing_rule_id"]) == EXPECTED_TIMING_RULES
    assert "PIT_ADMISSIBILITY_PASS_CANDIDATE" in set(statuses["status_name"])
    assert FORBIDDEN_FUTURE_STATUSES.isdisjoint(set(statuses["status_name"]))
    assert (statuses["active_replay_input_allowed"] == "False").all()
    assert (statuses["trading_allowed"] == "False").all()


def test_forbidden_interpretations_safety_flags_and_next_task_are_bounded(tmp_path: Path) -> None:
    result = _build(tmp_path)
    forbidden = _csv(result, "forbidden_interpretation_matrix")
    safety = json.loads(result.artifact_paths["safety_flags"].read_text(encoding="utf-8"))
    report = result.artifact_paths["report"].read_text(encoding="utf-8")
    limitations = result.artifact_paths["limitations"].read_text(encoding="utf-8")
    next_task = result.artifact_paths["recommended_next_task"].read_text(encoding="utf-8")
    all_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in result.artifact_paths["artifact_dir"].iterdir()
        if path.suffix in {".json", ".csv", ".md"}
    )

    for flag in SAFETY_FALSE_FLAGS:
        assert safety[flag] is False
    assert "real_reviewed_csv_package_created" in set(forbidden["forbidden_interpretation"])
    assert "pit_admissibility_validator_implemented" in set(forbidden["forbidden_interpretation"])
    assert "future_labels_joined_to_training_dataset" in set(forbidden["forbidden_interpretation"])
    assert "No real reviewed CSV package is created" in report
    assert "No PIT admissibility validator is implemented" in report
    assert "reviewer approval does not override PIT failure" in limitations
    assert "Tiny PIT Admissibility Validator Contract Fixture Views Report-Only v0.1" in next_task
    assert not re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", all_text.lower())


def test_cli_command_runs_and_claims_no_real_workflows(tmp_path: Path) -> None:
    output_dir = (
        tmp_path
        / "outputs"
        / "reports"
        / "manual_diagnostics"
        / "tiny_pit_admissibility_validator_contract_fixture_v0_1"
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "tiny-pit-admissibility-validator-contract-fixture",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "tiny_pit_admissibility_validator_contract_fixture_id:" in completed.stdout
    assert "status: PASS" in completed.stdout
    assert f"workflow_stage: {TINY_PIT_ADMISSIBILITY_VALIDATOR_CONTRACT_FIXTURE_CREATED}" in completed.stdout
    assert "case_count: 12" in completed.stdout
    assert "package_section_count: 12" in completed.stdout
    assert "No real reviewed CSV package" in completed.stdout
    assert "No PIT admissibility validator" in completed.stdout
    assert "No data/raw, data/processed, or data/cache writes" in completed.stdout

    artifact_dirs = [path for path in output_dir.iterdir() if path.is_dir()]
    assert len(artifact_dirs) == 1
    assert (artifact_dirs[0] / "gate_case_matrix.csv").exists()

    help_output = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout
    assert "tiny-pit-admissibility-validator-contract-fixture" in help_output
