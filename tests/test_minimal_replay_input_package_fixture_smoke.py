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
from quant_replay_system.minimal_replay_input_package_fixture_smoke_health import (
    check_minimal_replay_input_package_fixture_smoke_health,
)
from quant_replay_system.minimal_replay_input_package_fixture_smoke_index import (
    build_minimal_replay_input_package_fixture_smoke_index,
)
from quant_replay_system.minimal_replay_input_package_fixture_smoke_status import (
    SMOKE_PASS_CANDIDATE_READY,
    run_minimal_replay_input_package_fixture_smoke_status,
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


def test_smoke_remains_manual_diagnostics_only_without_project_sources(tmp_path: Path) -> None:
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

    assert not Path("docs/project_sources").exists()


def test_smoke_index_discovers_artifact_and_validator_metadata(tmp_path: Path) -> None:
    smoke = run_minimal_replay_input_package_fixture_smoke(
        MinimalReplayInputPackageFixtureSmokeSettings(
            output_dir=_smoke_output_dir(tmp_path),
            validator_output_dir=_validator_output_dir(tmp_path),
        )
    )

    result = build_minimal_replay_input_package_fixture_smoke_index(
        root=_smoke_output_dir(tmp_path),
        output_dir=_smoke_output_dir(tmp_path) / "index",
    )

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["smoke_run_id"] == smoke.smoke_run_id
    assert row["validator_run_id"] == smoke.validator_run_id
    assert row["validator_status"] == REPLAY_INPUT_GATE_PASS_CANDIDATE
    assert row["validator_workflow_stage"] == REPLAY_INPUT_GATE_PASS_CANDIDATE
    assert row["pass_candidate"] is True
    assert row["active_replay_input_ready"] is False
    assert row["input_package_path"] == str(smoke.package_path)
    assert row["validator_artifact_path"] == str(smoke.validator_artifact_path)
    assert result.artifact_paths["index_csv"].exists()


def test_smoke_health_passes_for_valid_pass_candidate_artifact(tmp_path: Path) -> None:
    run_minimal_replay_input_package_fixture_smoke(
        MinimalReplayInputPackageFixtureSmokeSettings(
            output_dir=_smoke_output_dir(tmp_path),
            validator_output_dir=_validator_output_dir(tmp_path),
        )
    )

    result = check_minimal_replay_input_package_fixture_smoke_health(
        root=_smoke_output_dir(tmp_path),
        output_dir=_smoke_output_dir(tmp_path) / "health",
    )

    assert result.status == "PASS"
    assert result.error_count == 0
    assert result.issue_count == 0
    assert result.artifact_paths["health_csv"].exists()


def test_smoke_health_fails_if_validator_status_is_not_pass_candidate(tmp_path: Path) -> None:
    smoke = _write_smoke(tmp_path)
    _mutate_smoke_metadata(smoke.artifact_paths["smoke_metadata"], {"validator_status": "NO_INPUT"})

    result = check_minimal_replay_input_package_fixture_smoke_health(
        root=_smoke_output_dir(tmp_path),
        output_dir=_smoke_output_dir(tmp_path) / "health",
    )

    assert result.status == "FAIL"
    assert "VALIDATOR_NOT_PASS_CANDIDATE" in set(result.health_frame["issue_code"])


def test_smoke_health_fails_if_pass_candidate_is_false(tmp_path: Path) -> None:
    smoke = _write_smoke(tmp_path)
    _mutate_smoke_metadata(smoke.artifact_paths["smoke_metadata"], {"pass_candidate": False})

    result = check_minimal_replay_input_package_fixture_smoke_health(
        root=_smoke_output_dir(tmp_path),
        output_dir=_smoke_output_dir(tmp_path) / "health",
    )

    assert result.status == "FAIL"
    assert "PASS_CANDIDATE_FALSE" in set(result.health_frame["issue_code"])


def test_smoke_health_fails_for_unsafe_active_or_downstream_flags(tmp_path: Path) -> None:
    expected_codes = {
        "active_replay_input_ready": "ACTIVE_REPLAY_INPUT_READY_UNEXPECTED",
        "active_replay_input": "ACTIVE_REPLAY_INPUT_UNEXPECTED",
        "forward_labels_exist": "FORWARD_LABELS_EXIST_UNEXPECTED",
        "weights_trained": "WEIGHTS_TRAINED_UNEXPECTED",
        "active_stock_profile_exists": "ACTIVE_STOCK_PROFILE_EXISTS_UNEXPECTED",
        "real_buy_review_eligible": "REAL_BUY_REVIEW_ELIGIBLE_UNEXPECTED",
        "order_placed": "ORDER_PLACED_UNEXPECTED",
        "cache_mutated": "CACHE_MUTATED_UNEXPECTED",
    }
    for field, code in expected_codes.items():
        case_root = tmp_path / field
        smoke = run_minimal_replay_input_package_fixture_smoke(
            MinimalReplayInputPackageFixtureSmokeSettings(
                output_dir=_smoke_output_dir(case_root),
                validator_output_dir=_validator_output_dir(case_root),
            )
        )
        _mutate_smoke_metadata(smoke.artifact_paths["smoke_metadata"], {field: True})

        result = check_minimal_replay_input_package_fixture_smoke_health(
            root=_smoke_output_dir(case_root),
            output_dir=_smoke_output_dir(case_root) / "health",
        )

        assert result.status == "FAIL"
        assert code in set(result.health_frame["issue_code"])


def test_smoke_health_fails_for_unsafe_artifact_path(tmp_path: Path) -> None:
    smoke = _write_smoke(tmp_path)
    _mutate_smoke_metadata(smoke.artifact_paths["smoke_metadata"], {"artifact_path": str(tmp_path / "outside")})

    result = check_minimal_replay_input_package_fixture_smoke_health(
        root=_smoke_output_dir(tmp_path),
        output_dir=_smoke_output_dir(tmp_path) / "health",
    )

    assert result.status == "FAIL"
    assert "UNSAFE_ARTIFACT_PATH" in set(result.health_frame["issue_code"])


def test_smoke_status_reports_pass_candidate_ready_with_safety_text(tmp_path: Path) -> None:
    smoke = _write_smoke(tmp_path)

    result = run_minimal_replay_input_package_fixture_smoke_status(
        root=_smoke_output_dir(tmp_path),
        output_dir=_smoke_output_dir(tmp_path) / "status",
    )

    assert result.latest_smoke_run_id == smoke.smoke_run_id
    assert result.latest_validator_run_id == smoke.validator_run_id
    assert result.validator_status == REPLAY_INPUT_GATE_PASS_CANDIDATE
    assert result.health_status == "PASS"
    assert result.workflow_stage == SMOKE_PASS_CANDIDATE_READY
    assert result.pass_candidate is True
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert "report-only" in result.safety_statement
    assert "not active replay input" in result.safety_statement
    assert "not ACTIVE_REPLAY_INPUT_READY" in result.safety_statement
    assert "does not run replay" in result.safety_statement
    assert "does not compute forward labels" in result.safety_statement
    assert "does not train weights" in result.safety_statement
    assert "does not create active stock profiles" in result.safety_statement
    assert "does not create real buy-review eligibility" in result.safety_statement
    assert "does not authorize trading" in result.safety_statement


def test_smoke_artifact_view_cli_commands_run(tmp_path: Path) -> None:
    run_minimal_replay_input_package_fixture_smoke(
        MinimalReplayInputPackageFixtureSmokeSettings(
            output_dir=_smoke_output_dir(tmp_path),
            validator_output_dir=_validator_output_dir(tmp_path),
        )
    )

    commands = [
        ("minimal-replay-input-package-fixture-smoke-index", "artifact_count: 1"),
        ("minimal-replay-input-package-fixture-smoke-health", "status: PASS"),
        ("minimal-replay-input-package-fixture-smoke-status", "workflow_stage: SMOKE_PASS_CANDIDATE_READY"),
    ]
    for command, expected_text in commands:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "quant_replay_system.cli",
                command,
                "--root",
                str(_smoke_output_dir(tmp_path)),
                "--output-dir",
                str(_smoke_output_dir(tmp_path) / command.rsplit("-", 1)[-1]),
            ],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
        )
        assert expected_text in completed.stdout

    dashboard_source = Path("src/quant_replay_system/local_research_dashboard.py").read_text(encoding="utf-8")
    assert "minimal_replay_input_package_fixture_smoke_status" in dashboard_source
    assert not Path("docs/project_sources").exists()


def test_v1_30_docs_checkpoint_and_source_note_describe_smoke_safety() -> None:
    docs = {
        "smoke_doc": Path("docs/minimal_replay_input_package_fixture_smoke.md"),
        "dashboard_doc": Path("docs/local_research_dashboard.md"),
        "readme": Path("README.md"),
        "checkpoint": Path("docs/release_checkpoint_v1.30.0.md"),
        "source_note": Path("SOURCE_UPDATE_NOTES_v1_30_0.md"),
    }
    required_phrases = [
        "minimal-replay-input-package-fixture-smoke",
        "minimal-replay-input-package-fixture-smoke-index",
        "minimal-replay-input-package-fixture-smoke-health",
        "minimal-replay-input-package-fixture-smoke-status",
        "REPLAY_INPUT_GATE_PASS_CANDIDATE",
        "SMOKE_PASS_CANDIDATE_READY",
        "ACTIVE_REPLAY_INPUT_READY",
        "not active replay input",
        "does not run replay",
        "does not compute forward labels",
        "does not train weights",
        "does not create active stock profiles",
        "does not create real buy-review eligibility",
    ]

    for path in docs.values():
        assert path.exists(), path
    for name, path in docs.items():
        text = path.read_text(encoding="utf-8")
        for phrase in required_phrases:
            assert phrase in text, f"{phrase!r} missing from {name}"

    source_note = docs["source_note"].read_text(encoding="utf-8")
    assert "docs/project_sources/ is intentionally absent from Git" in source_note
    assert "ChatGPT Project Source is maintained separately" in source_note
    assert "after tag v1.30.0" in source_note
    assert not Path("docs/project_sources").exists()


def _smoke_output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "minimal_replay_input_package_fixture_smoke_v0_1"


def _validator_output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "historical_replay_input_gate_validator_v0_1"


def _is_under_manual_diagnostics(path: Path) -> bool:
    return "outputs/reports/manual_diagnostics" in str(path).replace("\\", "/")


def _write_smoke(tmp_path: Path):
    return run_minimal_replay_input_package_fixture_smoke(
        MinimalReplayInputPackageFixtureSmokeSettings(
            output_dir=_smoke_output_dir(tmp_path),
            validator_output_dir=_validator_output_dir(tmp_path),
        )
    )


def _mutate_smoke_metadata(metadata_path: Path, updates: dict[str, object]) -> None:
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.update(updates)
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
