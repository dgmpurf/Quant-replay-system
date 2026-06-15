from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from quant_replay_system.active_replay_input_create import (
    ACTIVE_REPLAY_INPUT_CREATED,
    ACTIVE_REPLAY_INPUT_CREATION_ATTESTATION_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_AUTHORITY_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_EVIDENCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_LINEAGE_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_OVERCLAIM_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_PIT_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_REVIEW_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_SOURCE_BLOCKED,
    ACTIVE_REPLAY_INPUT_CREATION_TAXONOMY_BLOCKED,
    NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT,
    READY_FOR_ACTIVE_REPLAY_INPUT_CREATION,
    ActiveReplayInputCreateSettings,
    run_active_replay_input_create,
)
from quant_replay_system.active_replay_input_create_health import (
    check_active_replay_input_create_health,
)
from quant_replay_system.active_replay_input_create_index import (
    build_active_replay_input_create_index,
)
from quant_replay_system.active_replay_input_create_status import (
    ACTIVE_REPLAY_INPUT_CREATE_CREATED,
    ACTIVE_REPLAY_INPUT_CREATE_NO_INPUT,
    READY_FOR_ACTIVE_REPLAY_INPUT_CREATE_REVIEW,
    run_active_replay_input_create_status,
)


def test_no_input_writes_required_artifacts_with_safe_defaults(tmp_path: Path) -> None:
    result = run_active_replay_input_create(
        ActiveReplayInputCreateSettings(output_dir=_output_dir(tmp_path))
    )

    assert result.status == NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT
    assert result.workflow_stage == NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT
    assert result.active_replay_input_created is False
    assert result.active_replay_input is False
    _assert_downstream_flags_false(result)
    assert result.report_only is True
    assert result.diagnostic_only is True

    for key in _required_artifact_keys():
        assert result.artifact_paths[key].exists()

    metadata = _read_json(result.artifact_paths["metadata"])
    assert metadata["active_input_creation_run_id"] == result.active_input_creation_run_id
    assert metadata["status"] == NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT
    assert metadata["active_replay_input_created"] is False
    assert metadata["active_replay_input"] is False
    for field in _downstream_false_fields():
        assert metadata[field] is False

    active_input = _read_json(result.artifact_paths["active_replay_input"])
    assert active_input["input_status"] == NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT
    assert active_input["active_replay_input_created"] is False
    assert active_input["active_replay_input"] is False
    assert active_input["report_only"] is True
    assert active_input["diagnostic_only"] is True


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("marker_artifact_path", ACTIVE_REPLAY_INPUT_CREATION_LINEAGE_BLOCKED),
        ("marker_health_artifact_path", ACTIVE_REPLAY_INPUT_CREATION_LINEAGE_BLOCKED),
        ("marker_status_artifact_path", ACTIVE_REPLAY_INPUT_CREATION_LINEAGE_BLOCKED),
        ("active_input_creation_plan_path", ACTIVE_REPLAY_INPUT_CREATION_REVIEW_BLOCKED),
        ("active_input_creation_request_manifest_path", ACTIVE_REPLAY_INPUT_CREATION_REVIEW_BLOCKED),
        ("active_input_authority_manifest_path", ACTIVE_REPLAY_INPUT_CREATION_AUTHORITY_BLOCKED),
        ("second_reviewer_attestation_manifest_path", ACTIVE_REPLAY_INPUT_CREATION_ATTESTATION_BLOCKED),
        ("pit_source_evidence_bundle_path", ACTIVE_REPLAY_INPUT_CREATION_EVIDENCE_BLOCKED),
        ("taxonomy_evidence_bundle_path", ACTIVE_REPLAY_INPUT_CREATION_TAXONOMY_BLOCKED),
        ("source_hash_revision_available_time_evidence_path", ACTIVE_REPLAY_INPUT_CREATION_SOURCE_BLOCKED),
        ("leakage_side_effect_evidence_bundle_path", ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", ACTIVE_REPLAY_INPUT_CREATION_OVERCLAIM_BLOCKED),
        ("active_replay_input_candidate_manifest_path", ACTIVE_REPLAY_INPUT_CREATION_EVIDENCE_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(
    tmp_path: Path, setting_name: str, expected_status: str
) -> None:
    settings = replace(_happy_settings(tmp_path), **{setting_name: None})

    result = run_active_replay_input_create(settings)

    assert result.status == expected_status
    assert result.active_replay_input_created is False
    assert result.active_replay_input is False
    _assert_downstream_flags_false(result)


@pytest.mark.parametrize(
    ("path_name", "override", "expected_status"),
    [
        (
            "marker_artifact_path",
            {"marker_status": "NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT"},
            ACTIVE_REPLAY_INPUT_CREATION_LINEAGE_BLOCKED,
        ),
        (
            "marker_artifact_path",
            {"active_replay_input_ready_marker_emitted": False},
            ACTIVE_REPLAY_INPUT_CREATION_LINEAGE_BLOCKED,
        ),
        (
            "marker_artifact_path",
            {"marker_file_exists": True, "active_replay_input_ready_marker_emitted": False},
            ACTIVE_REPLAY_INPUT_CREATION_LINEAGE_BLOCKED,
        ),
        (
            "marker_health_artifact_path",
            {"health_status": "FAIL"},
            ACTIVE_REPLAY_INPUT_CREATION_LINEAGE_BLOCKED,
        ),
        (
            "active_input_creation_request_manifest_path",
            {"explicit_active_replay_input_creation_request": False},
            ACTIVE_REPLAY_INPUT_CREATION_REVIEW_BLOCKED,
        ),
        (
            "active_input_authority_manifest_path",
            {"authority_result": "REJECTED"},
            ACTIVE_REPLAY_INPUT_CREATION_AUTHORITY_BLOCKED,
        ),
        (
            "second_reviewer_attestation_manifest_path",
            {"second_reviewer_attested": False},
            ACTIVE_REPLAY_INPUT_CREATION_ATTESTATION_BLOCKED,
        ),
        (
            "pit_source_evidence_bundle_path",
            {"accepted_pit_universe_evidence_attached": False},
            ACTIVE_REPLAY_INPUT_CREATION_PIT_BLOCKED,
        ),
        (
            "pit_source_evidence_bundle_path",
            {"source_registry_evidence_attached": False},
            ACTIVE_REPLAY_INPUT_CREATION_SOURCE_BLOCKED,
        ),
        (
            "pit_source_evidence_bundle_path",
            {"evidence_bundle_attached": False},
            ACTIVE_REPLAY_INPUT_CREATION_EVIDENCE_BLOCKED,
        ),
        (
            "taxonomy_evidence_bundle_path",
            {"not_fixed_12_only": False},
            ACTIVE_REPLAY_INPUT_CREATION_TAXONOMY_BLOCKED,
        ),
        (
            "source_hash_revision_available_time_evidence_path",
            {"source_hash_coverage_attached": False},
            ACTIVE_REPLAY_INPUT_CREATION_SOURCE_BLOCKED,
        ),
        (
            "leakage_side_effect_evidence_bundle_path",
            {"no_future_labels": False},
            ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED,
        ),
        (
            "leakage_side_effect_evidence_bundle_path",
            {"no_data_raw_written": False},
            ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED,
        ),
        (
            "overclaim_evidence_bundle_path",
            {"active_input_not_replay_permission": False},
            ACTIVE_REPLAY_INPUT_CREATION_OVERCLAIM_BLOCKED,
        ),
    ],
)
def test_manifest_gate_failures_block(
    tmp_path: Path, path_name: str, override: dict[str, object], expected_status: str
) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(getattr(settings, path_name), override)

    result = run_active_replay_input_create(settings)

    assert result.status == expected_status
    assert result.active_replay_input_created is False
    assert result.active_replay_input is False
    _assert_downstream_flags_false(result)


@pytest.mark.parametrize(
    ("unsafe_field", "expected_status"),
    [
        ("replay_execution_allowed", ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED),
        ("replay_decisions_exist", ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED),
        ("forward_labels_allowed", ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED),
        ("forward_labels_exist", ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED),
        ("forward_returns_exist", ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED),
        ("training_allowed", ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED),
        ("training_outputs_exist", ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED),
        ("model_weights_exist", ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED),
        ("weights_trained", ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED),
        ("stock_profile_allowed", ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED),
        ("stock_profile_artifacts_exist", ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED),
        ("active_stock_profile_exists", ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED),
        ("buy_review_allowed", ACTIVE_REPLAY_INPUT_CREATION_OVERCLAIM_BLOCKED),
        ("real_buy_review_eligible", ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED),
        ("trading_allowed", ACTIVE_REPLAY_INPUT_CREATION_OVERCLAIM_BLOCKED),
        ("order_placed", ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED),
        ("broker_api_called", ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED),
        ("message_sent", ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED),
        ("llm_api_called", ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED),
        ("external_api_called", ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED),
        ("cache_mutated", ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED),
        ("data_raw_written", ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED),
        ("data_processed_written", ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED),
        ("data_cache_written", ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED),
        ("current_candidates_run", ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED),
        ("snapshot_built", ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED),
        ("approved_for_paper", ACTIVE_REPLAY_INPUT_CREATION_OVERCLAIM_BLOCKED),
    ],
)
def test_unsafe_input_flags_block(tmp_path: Path, unsafe_field: str, expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.active_replay_input_candidate_manifest_path, {unsafe_field: True})

    result = run_active_replay_input_create(settings)

    assert result.status == expected_status
    assert result.active_replay_input_created is False
    assert result.active_replay_input is False
    _assert_downstream_flags_false(result)


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_active_replay_input_create(
            ActiveReplayInputCreateSettings(output_dir=tmp_path / "unsafe")
        )


def test_happy_path_without_allow_flag_reaches_ready_but_does_not_create_input(
    tmp_path: Path,
) -> None:
    result = run_active_replay_input_create(_happy_settings(tmp_path))

    assert result.status == READY_FOR_ACTIVE_REPLAY_INPUT_CREATION
    assert result.workflow_stage == READY_FOR_ACTIVE_REPLAY_INPUT_CREATION
    assert result.active_replay_input_created is False
    assert result.active_replay_input is False
    _assert_downstream_flags_false(result)

    active_input = _read_json(result.artifact_paths["active_replay_input"])
    assert active_input["input_status"] == READY_FOR_ACTIVE_REPLAY_INPUT_CREATION
    assert active_input["active_replay_input_created"] is False
    assert active_input["active_replay_input"] is False
    assert active_input["source_marker_run_id"] == "c5c065f6437a"
    assert active_input["marker_status"] == "ACTIVE_REPLAY_INPUT_READY"
    assert active_input["active_replay_input_ready_marker_emitted"] is True


def test_happy_path_with_explicit_allow_creates_report_only_active_input(tmp_path: Path) -> None:
    result = run_active_replay_input_create(
        replace(_happy_settings(tmp_path), allow_active_replay_input_creation=True)
    )

    assert result.status == ACTIVE_REPLAY_INPUT_CREATED
    assert result.workflow_stage == ACTIVE_REPLAY_INPUT_CREATED
    assert result.active_replay_input_created is True
    assert result.active_replay_input is True
    _assert_downstream_flags_false(result)

    active_input = _read_json(result.artifact_paths["active_replay_input"])
    assert active_input["active_replay_input_id"] == result.active_replay_input_id
    assert active_input["active_input_creation_run_id"] == result.active_input_creation_run_id
    assert active_input["input_status"] == ACTIVE_REPLAY_INPUT_CREATED
    assert active_input["active_replay_input_created"] is True
    assert active_input["active_replay_input"] is True
    assert active_input["source_marker_run_id"] == "c5c065f6437a"
    assert active_input["source_marker_artifact_path"] == str(_happy_marker_path(tmp_path))
    assert active_input["marker_status"] == "ACTIVE_REPLAY_INPUT_READY"
    assert active_input["marker_file_exists"] is True
    assert active_input["active_replay_input_ready_marker_emitted"] is True
    assert active_input["marker_only_semantics_confirmed"] is True
    assert active_input["replay_as_of_date"] == "2024-04-02"
    assert active_input["replay_calendar"] == "XSHG_XSHE_EOD"
    assert active_input["taxonomy_coverage"] == "8_LAYER_TAXONOMY_COVERED"
    assert active_input["leakage_check_status"] == "PASS"
    assert active_input["side_effect_check_status"] == "PASS"
    for field in _downstream_false_fields():
        assert active_input[field] is False
    assert active_input["report_only"] is True
    assert active_input["diagnostic_only"] is True

    report = result.artifact_paths["report"].read_text(encoding="utf-8")
    for phrase in [
        "not replay execution",
        "not replay decisions",
        "not forward labels",
        "not training",
        "not stock_profile",
        "not buy-review",
        "not trading",
    ]:
        assert phrase in report

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_cli_active_replay_input_create_no_input_runs(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "active-replay-input-create",
            "--output-dir",
            str(_output_dir(tmp_path)),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert f"status: {NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT}" in completed.stdout
    assert "active_replay_input_created: False" in completed.stdout
    assert "active_replay_input: False" in completed.stdout
    assert "replay_execution_allowed: False" in completed.stdout


def test_cli_happy_path_requires_explicit_allow_to_create_active_input(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    base_args = _cli_happy_args(settings)

    no_allow = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", *base_args],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    assert f"status: {READY_FOR_ACTIVE_REPLAY_INPUT_CREATION}" in no_allow.stdout
    assert "active_replay_input_created: False" in no_allow.stdout
    assert "active_replay_input: False" in no_allow.stdout

    allow = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            *base_args,
            "--allow-active-replay-input-creation",
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    assert f"status: {ACTIVE_REPLAY_INPUT_CREATED}" in allow.stdout
    assert "active_replay_input_created: True" in allow.stdout
    assert "active_replay_input: True" in allow.stdout
    for field in _downstream_false_fields():
        assert f"{field}: False" in allow.stdout


def test_cli_view_commands_are_added_without_research_status_or_checkpoint() -> None:
    help_text = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout

    assert "active-replay-input-create" in help_text
    assert "active-replay-input-create-index" in help_text
    assert "active-replay-input-create-health" in help_text
    assert "active-replay-input-create-status" in help_text
    assert "latest_active_replay_input_create" not in help_text
    assert not Path("docs/release_checkpoint_v1.40.0.md").exists()
    assert not Path("SOURCE_UPDATE_NOTES_v1_40_0.md").exists()
    assert not Path("docs/project_sources").exists()


def test_index_discovers_no_input_ready_and_created_artifacts(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    no_input = run_active_replay_input_create(ActiveReplayInputCreateSettings(output_dir=root))
    ready = run_active_replay_input_create(_happy_settings(tmp_path))
    created = run_active_replay_input_create(
        replace(_happy_settings(tmp_path), allow_active_replay_input_creation=True)
    )

    result = build_active_replay_input_create_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 3
    rows = {row["active_input_creation_run_id"]: row for row in result.index_frame.to_dict("records")}
    assert rows[no_input.active_input_creation_run_id]["status"] == NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT
    assert rows[ready.active_input_creation_run_id]["status"] == READY_FOR_ACTIVE_REPLAY_INPUT_CREATION
    assert rows[created.active_input_creation_run_id]["status"] == ACTIVE_REPLAY_INPUT_CREATED
    assert rows[no_input.active_input_creation_run_id]["active_replay_input_file_exists"] is True
    assert rows[ready.active_input_creation_run_id]["active_replay_input_file_exists"] is True
    assert rows[created.active_input_creation_run_id]["active_replay_input_file_exists"] is True
    assert rows[created.active_input_creation_run_id]["source_marker_run_id"] == "c5c065f6437a"
    assert rows[created.active_input_creation_run_id]["marker_status"] == "ACTIVE_REPLAY_INPUT_READY"
    assert rows[created.active_input_creation_run_id]["active_replay_input_created"] is True
    assert rows[created.active_input_creation_run_id]["active_replay_input"] is True
    for field in _downstream_false_fields():
        assert rows[created.active_input_creation_run_id][field] is False


@pytest.mark.parametrize(
    "settings_factory",
    [
        lambda tmp_path: ActiveReplayInputCreateSettings(output_dir=_output_dir(tmp_path)),
        lambda tmp_path: _happy_settings(tmp_path),
        lambda tmp_path: replace(_happy_settings(tmp_path), allow_active_replay_input_creation=True),
    ],
)
def test_health_passes_for_valid_active_input_create_artifacts(tmp_path: Path, settings_factory) -> None:
    root = _output_dir(tmp_path)
    run_active_replay_input_create(settings_factory(tmp_path))

    result = check_active_replay_input_create_health(root=root, output_dir=root / "health")

    assert result.status == "PASS"
    assert result.error_count == 0
    assert result.checked_artifact_count == 1


@pytest.mark.parametrize(
    ("metadata_override", "remove_active_input", "expected_issue"),
    [
        ({"status": ACTIVE_REPLAY_INPUT_CREATED}, True, "MISSING_ACTIVE_REPLAY_INPUT_FILE"),
        (
            {"status": ACTIVE_REPLAY_INPUT_CREATED, "active_replay_input_created": False},
            False,
            "CREATED_STATUS_WITHOUT_CREATED_FLAG",
        ),
        (
            {"status": ACTIVE_REPLAY_INPUT_CREATED, "active_replay_input": False},
            False,
            "CREATED_STATUS_WITHOUT_ACTIVE_INPUT_FLAG",
        ),
        ({"status": ACTIVE_REPLAY_INPUT_CREATED, "report_only": False}, False, "UNSAFE_REPORT_ONLY_FLAGS"),
        ({"status": ACTIVE_REPLAY_INPUT_CREATED, "diagnostic_only": False}, False, "UNSAFE_REPORT_ONLY_FLAGS"),
        (
            {"status": READY_FOR_ACTIVE_REPLAY_INPUT_CREATION, "active_replay_input": True},
            False,
            "ACTIVE_INPUT_TRUE_OUTSIDE_CREATED_STATUS",
        ),
        (
            {"status": READY_FOR_ACTIVE_REPLAY_INPUT_CREATION, "active_replay_input_created": True},
            False,
            "ACTIVE_INPUT_CREATED_TRUE_OUTSIDE_CREATED_STATUS",
        ),
        ({"replay_execution_allowed": True}, False, "REPLAY_EXECUTION_ALLOWED_UNEXPECTED"),
        ({"replay_decisions_exist": True}, False, "REPLAY_DECISIONS_EXIST_UNEXPECTED"),
        ({"forward_labels_allowed": True}, False, "FORWARD_LABELS_ALLOWED_UNEXPECTED"),
        ({"forward_labels_exist": True}, False, "FORWARD_LABELS_EXIST_UNEXPECTED"),
        ({"training_allowed": True}, False, "TRAINING_ALLOWED_UNEXPECTED"),
        ({"weights_trained": True}, False, "WEIGHTS_TRAINED_UNEXPECTED"),
        ({"stock_profile_allowed": True}, False, "STOCK_PROFILE_ALLOWED_UNEXPECTED"),
        ({"active_stock_profile_exists": True}, False, "ACTIVE_STOCK_PROFILE_EXISTS_UNEXPECTED"),
        ({"buy_review_allowed": True}, False, "BUY_REVIEW_ALLOWED_UNEXPECTED"),
        ({"real_buy_review_eligible": True}, False, "REAL_BUY_REVIEW_ELIGIBLE_UNEXPECTED"),
        ({"trading_allowed": True}, False, "TRADING_ALLOWED_UNEXPECTED"),
        ({"order_placed": True}, False, "ORDER_PLACED_UNEXPECTED"),
        ({"broker_api_called": True}, False, "BROKER_API_CALLED_UNEXPECTED"),
        ({"message_sent": True}, False, "MESSAGE_SENT_UNEXPECTED"),
        ({"llm_api_called": True}, False, "LLM_API_CALLED_UNEXPECTED"),
        ({"external_api_called": True}, False, "EXTERNAL_API_CALLED_UNEXPECTED"),
        ({"cache_mutated": True}, False, "CACHE_MUTATED_UNEXPECTED"),
        ({"data_raw_written": True}, False, "DATA_RAW_WRITTEN_UNEXPECTED"),
        ({"data_processed_written": True}, False, "DATA_PROCESSED_WRITTEN_UNEXPECTED"),
        ({"data_cache_written": True}, False, "DATA_CACHE_WRITTEN_UNEXPECTED"),
        ({"current_candidates_run": True}, False, "CURRENT_CANDIDATES_RUN_UNEXPECTED"),
        ({"snapshot_built": True}, False, "SNAPSHOT_BUILT_UNEXPECTED"),
        ({"signal_semantics_changed": True}, False, "SIGNAL_SEMANTICS_CHANGED_UNEXPECTED"),
    ],
)
def test_health_fails_for_unsafe_active_input_create_artifacts(
    tmp_path: Path,
    metadata_override: dict[str, object],
    remove_active_input: bool,
    expected_issue: str,
) -> None:
    root = _output_dir(tmp_path)
    result = run_active_replay_input_create(
        replace(_happy_settings(tmp_path), allow_active_replay_input_creation=True)
    )
    _patch_json(result.artifact_paths["metadata"], metadata_override)
    if remove_active_input:
        result.artifact_paths["active_replay_input"].unlink()

    health = check_active_replay_input_create_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert expected_issue in set(health.health_frame["issue_code"])


def test_health_fails_when_overclaim_guards_fail(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    result = run_active_replay_input_create(
        replace(_happy_settings(tmp_path), allow_active_replay_input_creation=True)
    )
    _patch_json(result.artifact_paths["metadata"], {"overclaim_guard_pass_count": 1})

    health = check_active_replay_input_create_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "OVERCLAIM_GUARD_FAILED" in set(health.health_frame["issue_code"])


def test_status_reports_no_input_ready_and_created_states(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    no_input = run_active_replay_input_create(ActiveReplayInputCreateSettings(output_dir=root))
    no_input_status = run_active_replay_input_create_status(root=root, output_dir=root / "status")
    assert no_input_status.latest_active_replay_input_creation_run_id == no_input.active_input_creation_run_id
    assert no_input_status.workflow_stage == ACTIVE_REPLAY_INPUT_CREATE_NO_INPUT
    assert no_input_status.active_replay_input_created is False
    assert no_input_status.active_replay_input is False

    ready_root = tmp_path / "ready" / "outputs" / "reports" / "manual_diagnostics" / "active_replay_input_create_v0_1"
    ready = run_active_replay_input_create(replace(_happy_settings(tmp_path / "ready"), output_dir=ready_root))
    ready_status = run_active_replay_input_create_status(root=ready_root, output_dir=ready_root / "status")
    assert ready_status.latest_active_replay_input_creation_run_id == ready.active_input_creation_run_id
    assert ready_status.workflow_stage == READY_FOR_ACTIVE_REPLAY_INPUT_CREATE_REVIEW
    assert ready_status.active_replay_input_created is False
    assert ready_status.active_replay_input is False

    created_root = tmp_path / "created" / "outputs" / "reports" / "manual_diagnostics" / "active_replay_input_create_v0_1"
    created = run_active_replay_input_create(
        replace(_happy_settings(tmp_path / "created"), output_dir=created_root, allow_active_replay_input_creation=True)
    )
    created_status = run_active_replay_input_create_status(root=created_root, output_dir=created_root / "status")
    assert created_status.latest_active_replay_input_creation_run_id == created.active_input_creation_run_id
    assert created_status.workflow_stage == ACTIVE_REPLAY_INPUT_CREATE_CREATED
    assert created_status.active_replay_input_created is True
    assert created_status.active_replay_input is True
    assert created_status.active_replay_input_file_exists is True
    assert created_status.source_marker_run_id == "c5c065f6437a"
    assert created_status.marker_status == "ACTIVE_REPLAY_INPUT_READY"
    assert created_status.replay_execution_allowed is False
    assert created_status.replay_decisions_exist is False
    assert created_status.forward_labels_exist is False
    assert created_status.weights_trained is False
    assert created_status.active_stock_profile_exists is False
    assert created_status.real_buy_review_eligible is False
    assert created_status.trading_allowed is False
    for phrase in [
        "report-only",
        "diagnostic-only",
        "does not run replay",
        "does not create replay decisions",
        "does not compute labels",
        "does not train weights",
        "does not create stock_profile",
        "does not create buy-review eligibility",
        "does not authorize trading",
    ]:
        assert phrase in created_status.safety_statement


def test_cli_active_input_create_views_run(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    run_active_replay_input_create(
        replace(_happy_settings(tmp_path), allow_active_replay_input_creation=True)
    )
    env = {**os.environ, "PYTHONPATH": "src"}
    commands = [
        "active-replay-input-create-index",
        "active-replay-input-create-health",
        "active-replay-input-create-status",
    ]
    for command in commands:
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
        assert "active replay input" in completed.stdout.lower() or "status:" in completed.stdout.lower()


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "active_replay_input_create_v0_1"


def _fixture_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "active_replay_input_create_fixture_v0_1"


def _happy_marker_path(tmp_path: Path) -> Path:
    return _fixture_root(tmp_path) / "active_replay_input_ready_marker.json"


def _happy_settings(tmp_path: Path) -> ActiveReplayInputCreateSettings:
    root = _fixture_root(tmp_path)
    root.mkdir(parents=True, exist_ok=True)
    marker_path = _write_json(root / "active_replay_input_ready_marker.json", _marker_payload())
    health_path = _write_json(root / "marker_health.json", {"health_status": "PASS"})
    status_path = _write_json(root / "marker_status.json", _marker_status_payload())
    plan_path = root / "active_input_creation_plan.md"
    plan_path.write_text("# Report-only active replay input creation plan\n", encoding="utf-8")
    request_path = _write_json(root / "active_input_creation_request.json", _request_payload())
    authority_path = _write_json(root / "active_input_authority.json", _authority_payload())
    attestation_path = _write_json(root / "second_reviewer_attestation.json", _attestation_payload())
    pit_source_path = _write_json(root / "pit_source_evidence.json", _pit_source_payload())
    taxonomy_path = _write_json(root / "taxonomy_evidence.json", _taxonomy_payload())
    source_path = _write_json(root / "source_hash_revision_available_time.json", _source_hash_payload())
    leakage_path = _write_json(root / "leakage_side_effect.json", _leakage_payload())
    overclaim_path = _write_json(root / "overclaim.json", _overclaim_payload())
    candidate_path = _write_json(root / "active_replay_input_candidate.json", _candidate_payload(marker_path))
    return ActiveReplayInputCreateSettings(
        marker_artifact_path=marker_path,
        marker_health_artifact_path=health_path,
        marker_status_artifact_path=status_path,
        active_input_creation_plan_path=plan_path,
        active_input_creation_request_manifest_path=request_path,
        active_input_authority_manifest_path=authority_path,
        second_reviewer_attestation_manifest_path=attestation_path,
        pit_source_evidence_bundle_path=pit_source_path,
        taxonomy_evidence_bundle_path=taxonomy_path,
        source_hash_revision_available_time_evidence_path=source_path,
        leakage_side_effect_evidence_bundle_path=leakage_path,
        overclaim_evidence_bundle_path=overclaim_path,
        active_replay_input_candidate_manifest_path=candidate_path,
        output_dir=_output_dir(tmp_path),
    )


def _marker_payload() -> dict[str, object]:
    payload = {
        "actual_emission_run_id": "c5c065f6437a",
        "marker_status": "ACTIVE_REPLAY_INPUT_READY",
        "workflow_stage": "ACTIVE_REPLAY_INPUT_READY",
        "marker_file_exists": True,
        "active_replay_input_ready_marker_emitted": True,
        "active_replay_input_ready": True,
        "active_ready_emitted": True,
        "marker_only_semantics_confirmed": True,
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update({field: False for field in _downstream_false_fields()})
    payload.update(
        {
            "order_placed": False,
            "broker_api_called": False,
            "message_sent": False,
            "llm_api_called": False,
            "external_api_called": False,
            "cache_mutated": False,
            "data_raw_written": False,
            "data_processed_written": False,
            "data_cache_written": False,
            "current_candidates_run": False,
            "snapshot_built": False,
            "approved_for_paper": False,
        }
    )
    return payload


def _marker_status_payload() -> dict[str, object]:
    return {
        "status": "ACTIVE_REPLAY_INPUT_READY",
        "workflow_stage": "ACTIVE_REPLAY_INPUT_READY",
        "active_replay_input_ready_marker_emitted": True,
        "marker_file_exists": True,
        "marker_only_semantics_confirmed": True,
    }


def _request_payload() -> dict[str, object]:
    return {
        "request_result": "PASS",
        "explicit_active_replay_input_creation_request": True,
        "requested_input_status": ACTIVE_REPLAY_INPUT_CREATED,
        "report_only": True,
        "diagnostic_only": True,
        "request_text": (
            "Explicitly authorize creating a report-only active replay input artifact "
            "from marker-only ACTIVE_REPLAY_INPUT_READY lineage."
        ),
    }


def _authority_payload() -> dict[str, object]:
    return {
        "authority_result": "PASS",
        "primary_reviewer": "reviewer_a",
        "second_reviewer": "reviewer_b",
        "authorized_by": "reviewer_a",
        "authorized_at": "2026-06-15T00:00:00Z",
        "authority_scope": "REPORT_ONLY_ACTIVE_REPLAY_INPUT_CREATION",
        "authority_reason": "Create governed active input artifact only; no replay.",
        "report_only": True,
        "diagnostic_only": True,
    }


def _attestation_payload() -> dict[str, object]:
    return {
        "second_reviewer_attested": True,
        "active_input_creation_attested": True,
        "report_only_attested": True,
        "no_replay_execution_attested": True,
        "no_replay_decision_creation_attested": True,
        "no_forward_label_attested": True,
        "no_training_attested": True,
        "no_stock_profile_attested": True,
        "no_buy_review_attested": True,
        "no_trading_authority_attested": True,
        "no_performance_claim_attested": True,
        "report_only": True,
        "diagnostic_only": True,
    }


def _pit_source_payload() -> dict[str, object]:
    return {
        "accepted_pit_universe_evidence_attached": True,
        "source_registry_evidence_attached": True,
        "raw_document_store_attached": True,
        "evidence_bundle_attached": True,
        "source_id_coverage_attached": True,
        "source_hash_coverage_attached": True,
        "revision_id_coverage_attached": True,
        "available_time_policy_attached": True,
        "permission_class_coverage_attached": True,
        "report_only": True,
        "diagnostic_only": True,
    }


def _taxonomy_payload() -> dict[str, object]:
    return {
        "uses_8_layer_taxonomy": True,
        "not_fixed_12_only": True,
        "factor_definition_attached": True,
        "factor_observation_attached": True,
        "event_structured_attached": True,
        "company_exposure_attached": True,
        "factor_layer_metadata_attached": True,
        "taxonomy_coverage": "8_LAYER_TAXONOMY_COVERED",
        "report_only": True,
        "diagnostic_only": True,
    }


def _source_hash_payload() -> dict[str, object]:
    return {
        "source_hash_coverage_attached": True,
        "revision_id_coverage_attached": True,
        "available_time_policy_attached": True,
        "source_hash_coverage": "COMPLETE",
        "revision_id_coverage": "COMPLETE",
        "available_time_policy": "ALL_AVAILABLE_TIME_LTE_REPLAY_DECISION_TIME",
        "report_only": True,
        "diagnostic_only": True,
    }


def _leakage_payload() -> dict[str, object]:
    payload = {
        "no_future_labels": True,
        "no_forward_returns": True,
        "no_replay_decisions": True,
        "no_replay_execution": True,
        "no_training_outputs": True,
        "no_model_weights": True,
        "no_stock_profile_artifacts": True,
        "no_buy_review_eligibility": True,
        "no_approved_for_paper": True,
        "no_broker_api_called": True,
        "no_order_placed": True,
        "no_message_sent": True,
        "no_llm_api_called": True,
        "no_external_api_called": True,
        "no_cache_mutated": True,
        "no_data_raw_written": True,
        "no_data_processed_written": True,
        "no_data_cache_written": True,
        "no_current_candidates_run": True,
        "no_snapshot_built": True,
        "report_only": True,
        "diagnostic_only": True,
    }
    payload.update({field: False for field in _downstream_false_fields()})
    return payload


def _overclaim_payload() -> dict[str, object]:
    return {
        "active_input_not_replay_permission": True,
        "active_input_not_replay_decision_permission": True,
        "active_input_not_label_permission": True,
        "active_input_not_training_permission": True,
        "active_input_not_stock_profile_permission": True,
        "active_input_not_buy_review_eligibility": True,
        "active_input_not_paper_approval": True,
        "active_input_not_performance_validation": True,
        "active_input_not_trading_authorization": True,
        "marker_file_exists_not_sufficient": True,
        "marker_only_ready_not_active_input": True,
        "report_only": True,
        "diagnostic_only": True,
    }


def _candidate_payload(marker_path: Path) -> dict[str, object]:
    payload = {
        "source_marker_run_id": "c5c065f6437a",
        "source_marker_artifact_path": str(marker_path),
        "marker_status": "ACTIVE_REPLAY_INPUT_READY",
        "marker_file_exists": True,
        "active_replay_input_ready_marker_emitted": True,
        "marker_only_semantics_confirmed": True,
        "replay_as_of_date": "2024-04-02",
        "replay_calendar": "XSHG_XSHE_EOD",
        "symbol_universe_ref": "outputs/reports/manual_diagnostics/example/symbol_universe.json",
        "pit_universe_ref": "outputs/reports/manual_diagnostics/example/pit_universe.json",
        "source_registry_ref": "outputs/reports/manual_diagnostics/example/source_registry.json",
        "raw_document_store_ref": "outputs/reports/manual_diagnostics/example/raw_documents.json",
        "factor_definition_ref": "outputs/reports/manual_diagnostics/example/factor_definitions.json",
        "factor_observation_ref": "outputs/reports/manual_diagnostics/example/factor_observations.json",
        "event_structured_ref": "outputs/reports/manual_diagnostics/example/events.json",
        "company_exposure_ref": "outputs/reports/manual_diagnostics/example/exposures.json",
        "evidence_bundle_ref": "outputs/reports/manual_diagnostics/example/evidence_bundle.json",
        "source_hash_coverage": "COMPLETE",
        "revision_id_coverage": "COMPLETE",
        "available_time_policy": "ALL_AVAILABLE_TIME_LTE_REPLAY_DECISION_TIME",
        "taxonomy_coverage": "8_LAYER_TAXONOMY_COVERED",
        "leakage_check_status": "PASS",
        "side_effect_check_status": "PASS",
        "report_only": True,
        "diagnostic_only": True,
        "active_replay_input": False,
    }
    payload.update({field: False for field in _downstream_false_fields()})
    payload.update(
        {
            "order_placed": False,
            "broker_api_called": False,
            "message_sent": False,
            "llm_api_called": False,
            "external_api_called": False,
            "cache_mutated": False,
            "data_raw_written": False,
            "data_processed_written": False,
            "data_cache_written": False,
            "current_candidates_run": False,
            "snapshot_built": False,
            "approved_for_paper": False,
        }
    )
    return payload


def _cli_happy_args(settings: ActiveReplayInputCreateSettings) -> list[str]:
    return [
        "active-replay-input-create",
        "--marker-artifact-path",
        str(settings.marker_artifact_path),
        "--marker-health-artifact-path",
        str(settings.marker_health_artifact_path),
        "--marker-status-artifact-path",
        str(settings.marker_status_artifact_path),
        "--active-input-creation-plan-path",
        str(settings.active_input_creation_plan_path),
        "--active-input-creation-request-manifest-path",
        str(settings.active_input_creation_request_manifest_path),
        "--active-input-authority-manifest-path",
        str(settings.active_input_authority_manifest_path),
        "--second-reviewer-attestation-manifest-path",
        str(settings.second_reviewer_attestation_manifest_path),
        "--pit-source-evidence-bundle-path",
        str(settings.pit_source_evidence_bundle_path),
        "--taxonomy-evidence-bundle-path",
        str(settings.taxonomy_evidence_bundle_path),
        "--source-hash-revision-available-time-evidence-path",
        str(settings.source_hash_revision_available_time_evidence_path),
        "--leakage-side-effect-evidence-bundle-path",
        str(settings.leakage_side_effect_evidence_bundle_path),
        "--overclaim-evidence-bundle-path",
        str(settings.overclaim_evidence_bundle_path),
        "--active-replay-input-candidate-manifest-path",
        str(settings.active_replay_input_candidate_manifest_path),
        "--output-dir",
        str(settings.output_dir),
    ]


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _patch_json(path: Path, override: dict[str, object]) -> None:
    payload = _read_json(path)
    payload.update(override)
    _write_json(path, payload)


def _required_artifact_keys() -> list[str]:
    return [
        "metadata",
        "report",
        "precondition_results",
        "authority_results",
        "lineage_results",
        "attestation_results",
        "pit_source_evidence_results",
        "taxonomy_evidence_results",
        "leakage_side_effect_guard_results",
        "overclaim_guard_results",
        "active_replay_input",
        "recommended_next_task",
    ]


def _downstream_false_fields() -> list[str]:
    return [
        "replay_execution_allowed",
        "replay_decisions_exist",
        "forward_labels_allowed",
        "forward_labels_exist",
        "training_allowed",
        "weights_trained",
        "stock_profile_allowed",
        "active_stock_profile_exists",
        "buy_review_allowed",
        "real_buy_review_eligible",
        "trading_allowed",
    ]


def _assert_downstream_flags_false(result: object) -> None:
    for field in _downstream_false_fields():
        assert getattr(result, field) is False
