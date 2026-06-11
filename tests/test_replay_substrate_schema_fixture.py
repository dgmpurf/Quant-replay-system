from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import os
import json

import pandas as pd

from quant_replay_system.replay_substrate_schema_fixture import (
    REPLAY_SUBSTRATE_ENTITIES,
    build_replay_substrate_schema_fixture,
)
from quant_replay_system.replay_substrate_schema_fixture_health import (
    check_replay_substrate_schema_fixture_health,
)
from quant_replay_system.replay_substrate_schema_fixture_index import (
    build_replay_substrate_schema_fixture_index,
)
from quant_replay_system.replay_substrate_schema_fixture_status import (
    REPLAY_SUBSTRATE_SCHEMA_FIXTURE_READY,
    run_replay_substrate_schema_fixture_status,
)


def test_replay_substrate_schema_fixture_writes_diagnostic_outputs(tmp_path: Path) -> None:
    result = build_replay_substrate_schema_fixture(output_dir=tmp_path)

    assert result.status == "PASS"
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.entity_count == len(REPLAY_SUBSTRATE_ENTITIES)
    assert result.validation_issue_count == 0
    assert result.forward_labels_computed is False
    assert result.weights_trained is False
    assert result.active_stock_profile_created is False
    assert result.real_buy_review_eligible is False

    artifact_dir = result.artifact_paths["artifact_dir"]
    assert artifact_dir.is_relative_to(tmp_path)
    assert (artifact_dir / "replay_substrate_schema_fixture_report.md").exists()
    assert (artifact_dir / "schema_fixture_entity_status.csv").exists()
    assert (artifact_dir / "schema_fixture_validation_issues.csv").exists()
    assert (artifact_dir / "schema_fixture_overclaim_guards.csv").exists()
    assert (artifact_dir / "recommended_next_task.md").exists()

    entity_status = pd.read_csv(artifact_dir / "schema_fixture_entity_status.csv", dtype=str)
    assert set(entity_status["entity"]) == set(REPLAY_SUBSTRATE_ENTITIES)
    assert (entity_status["required_fields_present"] == "True").all()
    assert (entity_status["pit_fields_present"] == "True").all()
    assert (entity_status["permission_fields_present"] == "True").all()
    assert (entity_status["active_artifact_allowed"] == "False").all()


def test_fixture_samples_preserve_symbols_and_block_training_label_profile_states(tmp_path: Path) -> None:
    result = build_replay_substrate_schema_fixture(output_dir=tmp_path)
    sample_dir = result.artifact_paths["sample_rows_dir"]

    factor_observation = pd.read_csv(sample_dir / "factor_observation_fixture.csv", dtype=str)
    assert factor_observation.loc[0, "symbol"] == "000001"
    assert factor_observation.loc[0, "pit_valid"] == "True"

    forward_label = pd.read_csv(sample_dir / "forward_return_label_schema_fixture.csv", dtype=str)
    assert forward_label.loc[0, "label_status"] == "blocked_not_computed"
    assert forward_label.loc[0, "no_forward_labels_computed"] == "True"
    assert forward_label.loc[0, "label_value"] == "not_computed"

    training = pd.read_csv(sample_dir / "training_result_schema_fixture.csv", dtype=str)
    assert training.loc[0, "training_status"] == "research_only_blocked"
    assert training.loc[0, "no_weights_trained"] == "True"

    stock_profile = pd.read_csv(sample_dir / "stock_profile_schema_fixture.csv", dtype=str)
    assert stock_profile.loc[0, "symbol"] == "000001"
    assert stock_profile.loc[0, "paper_status"] == "not_validated"
    assert stock_profile.loc[0, "real_buy_review_eligible"] == "False"
    assert stock_profile.loc[0, "no_active_stock_profile_created"] == "True"


def test_overclaim_guards_all_pass(tmp_path: Path) -> None:
    result = build_replay_substrate_schema_fixture(output_dir=tmp_path)
    guards = pd.read_csv(result.artifact_paths["overclaim_guards"], dtype=str)

    assert set(guards["guard_name"]) == {
        "PIT preview cannot become approval",
        "factor observation cannot become alpha",
        "replay decision cannot claim performance",
        "forward label cannot leak into replay decision",
        "training result cannot become production validation",
        "stock profile cannot become buy permission",
        "LLM/event extraction cannot become deterministic signal",
        "real_buy_review_eligible must remain false",
    }
    assert (guards["passed"] == "True").all()


def test_cli_writes_fixture_outputs_under_requested_diagnostics_path(tmp_path: Path) -> None:
    output_dir = tmp_path / "manual_diagnostics" / "replay_substrate_schema_fixture_v0_1"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "replay-substrate-schema-fixture",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "fixture_id:" in completed.stdout
    assert "real_buy_review_eligible: False" in completed.stdout
    assert "No replay, current-candidates" in completed.stdout
    artifact_dirs = [path for path in output_dir.iterdir() if path.is_dir()]
    assert len(artifact_dirs) == 1
    assert (artifact_dirs[0] / "schema_fixture_entity_status.csv").exists()

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()


def test_replay_substrate_schema_fixture_index_discovers_fixture(tmp_path: Path) -> None:
    fixture = build_replay_substrate_schema_fixture(output_dir=tmp_path)

    result = build_replay_substrate_schema_fixture_index(root=tmp_path, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    assert result.index_frame.loc[0, "fixture_id"] == fixture.fixture_id
    assert result.index_frame.loc[0, "entity_count"] == 14
    assert result.index_frame.loc[0, "validation_issue_count"] == 0
    assert result.index_frame.loc[0, "overclaim_guard_pass_count"] == 8
    assert result.index_frame.loc[0, "overclaim_guard_total_count"] == 8
    assert result.index_frame.loc[0, "forward_labels_computed"] is False
    assert result.index_frame.loc[0, "weights_trained"] is False
    assert result.index_frame.loc[0, "active_stock_profile_created"] is False
    assert result.index_frame.loc[0, "real_buy_review_eligible"] is False
    assert (tmp_path / "index" / "replay_substrate_schema_fixture_index.csv").exists()


def test_replay_substrate_schema_fixture_health_passes_for_safe_fixture(tmp_path: Path) -> None:
    build_replay_substrate_schema_fixture(output_dir=tmp_path)

    result = check_replay_substrate_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0
    assert (tmp_path / "health").exists()


def test_replay_substrate_schema_fixture_health_fails_for_unsafe_or_missing_flags(tmp_path: Path) -> None:
    fixture = build_replay_substrate_schema_fixture(output_dir=tmp_path)
    metadata_path = fixture.artifact_paths["metadata"]
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.pop("no_live_trading")
    metadata["real_buy_review_eligible"] = True
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    result = check_replay_substrate_schema_fixture_health(root=tmp_path, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert set(result.health_frame["issue_code"]) >= {
        "MISSING_SAFETY_FLAGS",
        "REAL_BUY_REVIEW_ELIGIBLE_UNEXPECTED",
    }


def test_replay_substrate_schema_fixture_status_summarizes_latest_fixture(tmp_path: Path) -> None:
    fixture = build_replay_substrate_schema_fixture(output_dir=tmp_path)

    result = run_replay_substrate_schema_fixture_status(root=tmp_path, output_dir=tmp_path / "status")

    assert result.status == "PASS"
    assert result.workflow_stage == REPLAY_SUBSTRATE_SCHEMA_FIXTURE_READY
    assert result.latest_fixture_id == fixture.fixture_id
    assert result.entity_count == 14
    assert result.validation_issue_count == 0
    assert result.overclaim_guard_status == "PASS"
    assert result.overclaim_guard_pass_count == 8
    assert result.overclaim_guard_total_count == 8
    assert result.active_replay_input is False
    assert result.forward_labels_exist is False
    assert result.weights_trained is False
    assert result.active_stock_profile_exists is False
    assert result.real_buy_review_eligible is False
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.no_live_trading is True
    assert result.no_broker_api is True
    assert result.no_order_placement is True
    assert "report-only replay substrate schema fixture" in result.next_manual_action


def test_replay_substrate_schema_fixture_view_clis_work(tmp_path: Path) -> None:
    root = tmp_path / "manual_diagnostics" / "replay_substrate_schema_fixture_v0_1"
    build_replay_substrate_schema_fixture(output_dir=root)

    env = {**os.environ, "PYTHONPATH": "src"}
    for command in [
        "replay-substrate-schema-fixture-index",
        "replay-substrate-schema-fixture-health",
        "replay-substrate-schema-fixture-status",
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
            env=env,
        )
        assert "No replay, current-candidates" in completed.stdout


def test_replay_substrate_schema_fixture_checkpoint_doc_records_safety_boundaries() -> None:
    checkpoint = Path("docs/release_checkpoint_v1.27.0.md")
    text = checkpoint.read_text(encoding="utf-8")

    assert "This checkpoint does not validate strategy performance." in text
    assert "This checkpoint does not compute forward labels." in text
    assert "This checkpoint does not train model weights." in text
    assert "This checkpoint does not create active stock profiles." in text
    assert "This checkpoint does not create real buy-review eligibility." in text
    assert "This checkpoint does not approve live trading or broker integration." in text
    assert "schema fixtures remain non-active" in text
