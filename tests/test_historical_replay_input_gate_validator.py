from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.historical_replay_input_gate_validator import (
    REPLAY_INPUT_GATE_PASS_CANDIDATE,
    run_historical_replay_input_gate_validator,
)


def test_no_input_returns_no_input_and_writes_report_only_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "historical_replay_input_gate_validator_v0_1"

    result = run_historical_replay_input_gate_validator(output_dir=output_dir)

    assert result.status == "NO_INPUT"
    assert result.pass_candidate is False
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.forward_labels_exist is False
    assert result.weights_trained is False
    assert result.active_stock_profile_exists is False
    assert result.real_buy_review_eligible is False
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_paths["artifact_dir"].is_relative_to(output_dir)

    for key in [
        "metadata",
        "input_gate_report",
        "input_package_summary",
        "gate_results",
        "blocker_matrix",
        "entity_contract_validation",
        "non_input_artifact_rejections",
        "overclaim_guard_report",
        "recommended_next_task",
    ]:
        assert result.artifact_paths[key].exists()

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == "NO_INPUT"
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["no_live_trading"] is True
    assert metadata["no_broker_api"] is True


def test_known_fixture_package_type_is_rejected_as_non_input_artifact(tmp_path: Path) -> None:
    package = _write_valid_package(tmp_path / "package", manifest_overrides={"package_type": "input_gate_validator_fixture"})

    result = run_historical_replay_input_gate_validator(input_package=package, output_dir=_output_dir(tmp_path))

    assert result.status == "NON_INPUT_ARTIFACT_REJECTED"
    assert result.pass_candidate is False
    assert result.active_replay_input_ready is False
    rejections = pd.read_csv(result.artifact_paths["non_input_artifact_rejections"], dtype=str)
    assert "input_gate_validator_fixture" in set(rejections["artifact_family"])


def test_missing_pit_universe_file_blocks_package(tmp_path: Path) -> None:
    package = _write_valid_package(tmp_path / "package", omit_files={"pit_universe.csv"})

    result = run_historical_replay_input_gate_validator(input_package=package, output_dir=_output_dir(tmp_path))

    assert result.status == "PIT_UNIVERSE_BLOCKED"
    assert result.pass_candidate is False
    blockers = pd.read_csv(result.artifact_paths["blocker_matrix"], dtype=str)
    assert "MISSING_REQUIRED_FILE" in set(blockers["blocker_reason"])


def test_not_accepted_pit_universe_blocks_package(tmp_path: Path) -> None:
    package = _write_valid_package(
        tmp_path / "package",
        manifest_overrides={"accepted_pit_universe": False, "approval_artifact_ref": ""},
    )

    result = run_historical_replay_input_gate_validator(input_package=package, output_dir=_output_dir(tmp_path))

    assert result.status == "PIT_UNIVERSE_BLOCKED"
    assert result.pass_candidate is False


def test_available_time_after_replay_decision_time_blocks_package(tmp_path: Path) -> None:
    package = _write_valid_package(
        tmp_path / "package",
        csv_overrides={
            "factor_observation.csv": {
                "available_time": "2024-04-03T09:30:00+08:00",
            }
        },
    )

    result = run_historical_replay_input_gate_validator(input_package=package, output_dir=_output_dir(tmp_path))

    assert result.status == "FACTOR_OBSERVATION_BLOCKED"
    blockers = pd.read_csv(result.artifact_paths["blocker_matrix"], dtype=str)
    assert "AVAILABLE_TIME_AFTER_DECISION_TIME" in set(blockers["blocker_reason"])


@pytest.mark.parametrize(
    ("column", "expected_status"),
    [
        ("permission_status", "SOURCE_REGISTRY_BLOCKED"),
        ("revision_id", "SOURCE_REGISTRY_BLOCKED"),
        ("source_hash", "SOURCE_REGISTRY_BLOCKED"),
    ],
)
def test_missing_source_registry_required_fields_block_package(
    tmp_path: Path, column: str, expected_status: str
) -> None:
    package = _write_valid_package(
        tmp_path / "package",
        csv_overrides={"source_registry.csv": {column: ""}},
    )

    result = run_historical_replay_input_gate_validator(input_package=package, output_dir=_output_dir(tmp_path))

    assert result.status == expected_status
    assert result.pass_candidate is False


def test_fixed_12_only_factor_definition_blocks_package(tmp_path: Path) -> None:
    package = _write_valid_package(
        tmp_path / "package",
        csv_overrides={"factor_definition.csv": {"fixed_12_only": "true"}},
    )

    result = run_historical_replay_input_gate_validator(input_package=package, output_dir=_output_dir(tmp_path))

    assert result.status == "FACTOR_DEFINITION_BLOCKED"
    blockers = pd.read_csv(result.artifact_paths["blocker_matrix"], dtype=str)
    assert "FIXED_12_ONLY_FACTOR_DEFINITION" in set(blockers["blocker_reason"])


@pytest.mark.parametrize(
    ("manifest_field", "manifest_value", "expected_status"),
    [
        ("forward_labels_exist", True, "FUTURE_LABEL_LEAKAGE_BLOCKED"),
        ("weights_trained", True, "TRAINING_LEAKAGE_BLOCKED"),
        ("active_stock_profile_exists", True, "STOCK_PROFILE_LEAKAGE_BLOCKED"),
        ("real_buy_review_eligible", True, "ACTIONABILITY_BLOCKED"),
        ("approval_applied", True, "ACTIONABILITY_BLOCKED"),
        ("order_placed", True, "ACTIONABILITY_BLOCKED"),
        ("llm_api_called", True, "ACTIONABILITY_BLOCKED"),
        ("external_api_called", True, "ACTIONABILITY_BLOCKED"),
        ("cache_mutated", True, "ACTIONABILITY_BLOCKED"),
        ("current_candidates_run", True, "ACTIONABILITY_BLOCKED"),
        ("snapshot_built", True, "ACTIONABILITY_BLOCKED"),
        ("signal_semantics_changed", True, "ACTIONABILITY_BLOCKED"),
    ],
)
def test_leakage_and_actionability_flags_block_package(
    tmp_path: Path, manifest_field: str, manifest_value: bool, expected_status: str
) -> None:
    package = _write_valid_package(tmp_path / "package", manifest_overrides={manifest_field: manifest_value})

    result = run_historical_replay_input_gate_validator(input_package=package, output_dir=_output_dir(tmp_path))

    assert result.status == expected_status
    assert result.pass_candidate is False
    assert result.active_replay_input_ready is False


def test_valid_minimal_local_package_returns_pass_candidate_only(tmp_path: Path) -> None:
    package = _write_valid_package(tmp_path / "package")

    result = run_historical_replay_input_gate_validator(input_package=package, output_dir=_output_dir(tmp_path))

    assert result.status == REPLAY_INPUT_GATE_PASS_CANDIDATE
    assert result.pass_candidate is True
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.forward_labels_exist is False
    assert result.weights_trained is False
    assert result.active_stock_profile_exists is False
    assert result.real_buy_review_eligible is False
    assert result.overclaim_guard_pass_count == result.overclaim_guard_total_count

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == REPLAY_INPUT_GATE_PASS_CANDIDATE
    assert metadata["pass_candidate"] is True
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["approval_applied"] is False
    assert metadata["order_placed"] is False

    gate_results = pd.read_csv(result.artifact_paths["gate_results"], dtype=str)
    assert "ACTIVE_REPLAY_INPUT_READY" not in set(gate_results["status"])
    assert (gate_results["active_ready_allowed_first"] == "False").all()

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_cli_command_runs_and_prints_report_only_summary(tmp_path: Path) -> None:
    package = _write_valid_package(tmp_path / "package")
    output_dir = _output_dir(tmp_path)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "historical-replay-input-gate-validator",
            "--input-package",
            str(package),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "validator_run_id:" in completed.stdout
    assert "status: REPLAY_INPUT_GATE_PASS_CANDIDATE" in completed.stdout
    assert "active_replay_input_ready: False" in completed.stdout
    assert "active_replay_input: False" in completed.stdout
    assert "No replay, current-candidates" in completed.stdout


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "historical_replay_input_gate_validator_v0_1"


def _write_valid_package(
    package_dir: Path,
    *,
    manifest_overrides: dict[str, object] | None = None,
    csv_overrides: dict[str, dict[str, object]] | None = None,
    omit_files: set[str] | None = None,
) -> Path:
    package_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "package_id": "real_replay_input_candidate_000001",
        "package_type": "historical_replay_input_package",
        "as_of_date": "2024-04-02",
        "replay_decision_time": "2024-04-02T16:00:00+08:00",
        "created_at": "2024-04-02T16:05:00+08:00",
        "accepted_pit_universe": True,
        "approval_artifact_ref": "accepted_pit_universe_artifact_001",
        "report_only": True,
        "diagnostic_only": True,
        "active_replay_input": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
        "approval_applied": False,
        "order_placed": False,
        "llm_api_called": False,
        "external_api_called": False,
        "cache_mutated": False,
        "current_candidates_run": False,
        "snapshot_built": False,
        "signal_semantics_changed": False,
    }
    manifest.update(manifest_overrides or {})
    (package_dir / "replay_input_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    rows_by_file: dict[str, dict[str, object]] = {
        "source_registry.csv": {
            "source_id": "src_official_001",
            "source_hash": "hash_source_001",
            "revision_id": "rev_source_001",
            "permission_status": "ACCEPTED_FOR_REPLAY_RESEARCH",
            "source_type": "OFFICIAL_PUBLIC",
        },
        "pit_universe.csv": {
            "signal_date": "2024-04-02",
            "symbol": "000001",
            "available_time": "2024-04-02T15:30:00+08:00",
            "source_id": "src_official_001",
            "source_hash": "hash_source_001",
            "revision_id": "rev_universe_001",
        },
        "raw_document_store.csv": {
            "document_id": "doc_000001_20240402",
            "publish_time": "2024-04-02T15:00:00+08:00",
            "available_time": "2024-04-02T15:30:00+08:00",
            "evidence_type": "OFFICIAL_STATUS",
            "source_id": "src_official_001",
            "source_hash": "hash_doc_001",
            "revision_id": "rev_doc_001",
        },
        "factor_definition.csv": {
            "factor_id": "event_quality_score",
            "factor_layer": "L1",
            "definition_revision_id": "rev_factor_def_001",
            "fixed_12_only": "false",
            "source_id": "src_official_001",
            "source_hash": "hash_factor_def_001",
            "revision_id": "rev_factor_def_001",
        },
        "factor_observation.csv": {
            "factor_id": "event_quality_score",
            "signal_date": "2024-04-02",
            "symbol": "000001",
            "observation_value": "0.5",
            "available_time": "2024-04-02T15:30:00+08:00",
            "source_id": "src_official_001",
            "source_hash": "hash_factor_obs_001",
            "revision_id": "rev_factor_obs_001",
        },
        "event_structured.csv": {
            "event_id": "event_000001_20240402",
            "event_type": "STATUS_CONTEXT",
            "publish_time": "2024-04-02T15:00:00+08:00",
            "available_time": "2024-04-02T15:30:00+08:00",
            "source_id": "src_official_001",
            "source_hash": "hash_event_001",
            "revision_id": "rev_event_001",
        },
        "company_exposure.csv": {
            "exposure_id": "exposure_000001_20240402",
            "symbol": "000001",
            "exposure_type": "industry",
            "exposure_value": "bank",
            "available_time": "2024-04-02T15:30:00+08:00",
            "source_id": "src_official_001",
            "source_hash": "hash_exposure_001",
            "revision_id": "rev_exposure_001",
        },
    }
    for file_name, overrides in (csv_overrides or {}).items():
        rows_by_file[file_name].update(overrides)
    for file_name, row in rows_by_file.items():
        if file_name in (omit_files or set()):
            continue
        pd.DataFrame([row], dtype=object).to_csv(package_dir / file_name, index=False)
    return package_dir
