from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system.historical_replay_input_gate_validator import REPLAY_INPUT_GATE_PASS_CANDIDATE
from quant_replay_system.minimal_replay_input_package_fixture_smoke import (
    MinimalReplayInputPackageFixtureSmokeSettings,
    run_minimal_replay_input_package_fixture_smoke,
)


def test_smoke_creates_minimal_package_and_runs_real_validator(tmp_path: Path) -> None:
    result = run_minimal_replay_input_package_fixture_smoke(
        MinimalReplayInputPackageFixtureSmokeSettings(
            output_dir=_smoke_output_dir(tmp_path),
            validator_output_dir=_validator_output_dir(tmp_path),
        )
    )

    assert result.validator_status == REPLAY_INPUT_GATE_PASS_CANDIDATE
    assert result.pass_candidate is True
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.forward_labels_exist is False
    assert result.weights_trained is False
    assert result.active_stock_profile_exists is False
    assert result.real_buy_review_eligible is False
    assert result.approval_applied is False
    assert result.order_placed is False
    assert result.llm_api_called is False
    assert result.external_api_called is False
    assert result.cache_mutated is False
    assert result.current_candidates_run is False
    assert result.snapshot_built is False
    assert result.signal_semantics_changed is False
    assert result.report_only is True
    assert result.diagnostic_only is True

    expected_files = {
        "input_package/replay_input_manifest.json",
        "input_package/source_registry.csv",
        "input_package/pit_universe.csv",
        "input_package/raw_document_store.csv",
        "input_package/factor_definition.csv",
        "input_package/factor_observation.csv",
        "input_package/event_structured.csv",
        "input_package/company_exposure.csv",
        "smoke_metadata.json",
        "smoke_report.md",
        "validator_result_ref.json",
        "expected_pass_candidate_conditions.csv",
        "safety_flag_report.csv",
        "recommended_next_task.md",
    }
    for relative_path in expected_files:
        assert (result.artifact_path / relative_path).exists()

    validator_metadata = json.loads((result.validator_artifact_path / "metadata.json").read_text(encoding="utf-8"))
    assert validator_metadata["status"] == REPLAY_INPUT_GATE_PASS_CANDIDATE
    assert validator_metadata["pass_candidate"] is True
    assert validator_metadata["active_replay_input_ready"] is False
    assert validator_metadata["active_replay_input"] is False


def test_smoke_package_contract_is_parseable_pit_safe_and_uses_8_layer_taxonomy(tmp_path: Path) -> None:
    result = run_minimal_replay_input_package_fixture_smoke(
        MinimalReplayInputPackageFixtureSmokeSettings(
            output_dir=_smoke_output_dir(tmp_path),
            validator_output_dir=_validator_output_dir(tmp_path),
        )
    )

    package = result.package_path
    manifest = json.loads((package / "replay_input_manifest.json").read_text(encoding="utf-8"))
    assert manifest["package_type"] == "historical_replay_input_package"
    assert manifest["accepted_pit_universe"] is True
    assert manifest["active_replay_input_ready"] is False
    assert manifest["active_replay_input"] is False
    assert manifest["real_buy_review_eligible"] is False
    assert manifest["report_only"] is True
    assert manifest["diagnostic_only"] is True

    decision_time = pd.to_datetime(manifest["replay_decision_time"], utc=True)
    for csv_path in package.glob("*.csv"):
        frame = pd.read_csv(csv_path, dtype=str).fillna("")
        assert not frame.empty
        if "symbol" in frame.columns:
            assert "000001" in set(frame["symbol"])
        for time_column in ["available_time", "publish_time"]:
            if time_column in frame.columns:
                observed = pd.to_datetime(frame[time_column], utc=True)
                assert (observed <= decision_time).all()

    factor_definition = pd.read_csv(package / "factor_definition.csv", dtype=str)
    assert set(factor_definition["factor_layer"]).issubset({f"L{index}" for index in range(1, 9)})
    assert factor_definition["fixed_12_only"].str.lower().eq("false").all()

    gate_results = pd.read_csv(result.validator_artifact_path / "gate_results.csv", dtype=str)
    assert "ACTIVE_REPLAY_INPUT_READY" not in set(gate_results["status"])


def test_smoke_cli_runs_and_prints_concise_summary(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "minimal-replay-input-package-fixture-smoke",
            "--output-dir",
            str(_smoke_output_dir(tmp_path)),
            "--validator-output-dir",
            str(_validator_output_dir(tmp_path)),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "smoke_run_id:" in completed.stdout
    assert "validator_status: REPLAY_INPUT_GATE_PASS_CANDIDATE" in completed.stdout
    assert "pass_candidate: True" in completed.stdout
    assert "active_replay_input_ready: False" in completed.stdout
    assert "active_replay_input: False" in completed.stdout
    assert "real_buy_review_eligible: False" in completed.stdout


def test_smoke_remains_manual_diagnostics_only_without_research_status_or_project_sources(tmp_path: Path) -> None:
    result = run_minimal_replay_input_package_fixture_smoke(
        MinimalReplayInputPackageFixtureSmokeSettings(
            output_dir=_smoke_output_dir(tmp_path),
            validator_output_dir=_validator_output_dir(tmp_path),
        )
    )

    assert _is_under_manual_diagnostics(result.artifact_path)
    assert _is_under_manual_diagnostics(result.package_path)
    assert _is_under_manual_diagnostics(result.validator_artifact_path)
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()

    dashboard_source = Path("src/quant_replay_system/local_research_dashboard.py").read_text(encoding="utf-8")
    assert "minimal_replay_input_package_fixture_smoke" not in dashboard_source
    assert not Path("docs/project_sources").exists()


def _smoke_output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "minimal_replay_input_package_fixture_smoke_v0_1"


def _validator_output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "historical_replay_input_gate_validator_v0_1"


def _is_under_manual_diagnostics(path: Path) -> bool:
    return "outputs/reports/manual_diagnostics" in str(path).replace("\\", "/")
