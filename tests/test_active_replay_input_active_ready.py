from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.active_replay_input_active_ready import (
    ACTIVE_READY_READY_FOR_FINAL_REVIEW,
    NO_ACTIVE_READY_INPUT,
    ActiveReplayInputActiveReadySettings,
    run_active_replay_input_active_ready,
)
from quant_replay_system.active_replay_input_active_ready_health import (
    check_active_replay_input_active_ready_health,
)
from quant_replay_system.active_replay_input_active_ready_index import (
    build_active_replay_input_active_ready_index,
)
from quant_replay_system.active_replay_input_active_ready_status import (
    ACTIVE_READY_HEALTH_FAILED,
    ACTIVE_READY_NO_INPUT,
    run_active_replay_input_active_ready_status,
)


def test_no_input_returns_no_active_ready_input_and_writes_required_artifacts(tmp_path: Path) -> None:
    result = run_active_replay_input_active_ready(
        ActiveReplayInputActiveReadySettings(output_dir=_active_ready_output_dir(tmp_path))
    )

    assert result.status == NO_ACTIVE_READY_INPUT
    assert result.ready_for_final_review is False
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.active_ready_emitted is False
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.artifact_path.is_relative_to(_active_ready_output_dir(tmp_path))

    for key in _required_artifact_keys():
        assert result.artifact_paths[key].exists()

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == NO_ACTIVE_READY_INPUT
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["active_ready_emitted"] is False
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert "ACTIVE_REPLAY_INPUT_READY" not in json.dumps(metadata)


def test_missing_acceptance_lineage_blocks(tmp_path: Path) -> None:
    result = run_active_replay_input_active_ready(
        ActiveReplayInputActiveReadySettings(
            output_dir=_active_ready_output_dir(tmp_path),
            acceptance_artifact=tmp_path / "missing_acceptance",
        )
    )

    assert result.status == "ACTIVE_READY_LINEAGE_BLOCKED"
    assert result.ready_for_final_review is False
    assert result.active_replay_input_ready is False


@pytest.mark.parametrize(
    ("field", "value", "expected_status"),
    [
        ("status", "NO_ACCEPTANCE_INPUT", "ACTIVE_READY_LINEAGE_BLOCKED"),
        ("ready_for_active_ready_review", False, "ACTIVE_READY_LINEAGE_BLOCKED"),
        ("active_replay_input_ready", True, "ACTIVE_READY_LEAKAGE_BLOCKED"),
        ("active_replay_input", True, "ACTIVE_READY_SIDE_EFFECT_BLOCKED"),
        ("active_ready_emitted", True, "ACTIVE_READY_LEAKAGE_BLOCKED"),
        ("forward_labels_exist", True, "ACTIVE_READY_LEAKAGE_BLOCKED"),
        ("weights_trained", True, "ACTIVE_READY_LEAKAGE_BLOCKED"),
        ("active_stock_profile_exists", True, "ACTIVE_READY_LEAKAGE_BLOCKED"),
        ("real_buy_review_eligible", True, "ACTIVE_READY_LEAKAGE_BLOCKED"),
    ],
)
def test_acceptance_metadata_blocks_non_ready_or_unsafe_state(
    tmp_path: Path, field: str, value: object, expected_status: str
) -> None:
    acceptance = _write_acceptance_artifact(tmp_path / "acceptance", {field: value})
    settings = _happy_settings(tmp_path, acceptance)

    result = run_active_replay_input_active_ready(settings)

    assert result.status == expected_status
    assert result.ready_for_final_review is False
    assert result.active_ready_emitted is False
    assert "ACTIVE_REPLAY_INPUT_READY" not in result.status


def test_acceptance_health_not_pass_blocks_when_health_artifact_is_provided(tmp_path: Path) -> None:
    acceptance = _write_acceptance_artifact(tmp_path / "acceptance")
    health = _write_json(tmp_path / "acceptance_health.json", {"health_status": "FAIL"})
    settings = _happy_settings(tmp_path, acceptance, acceptance_health_artifact=health)

    result = run_active_replay_input_active_ready(settings)

    assert result.status == "ACTIVE_READY_LINEAGE_BLOCKED"
    assert result.ready_for_final_review is False


def test_missing_active_ready_request_blocks(tmp_path: Path) -> None:
    acceptance = _write_acceptance_artifact(tmp_path / "acceptance")
    settings = _happy_settings(tmp_path, acceptance, active_ready_request_manifest=None)

    result = run_active_replay_input_active_ready(settings)

    assert result.status == "ACTIVE_READY_AUTHORITY_BLOCKED"
    assert result.ready_for_final_review is False


def test_unsafe_active_ready_request_side_effect_blocks(tmp_path: Path) -> None:
    acceptance = _write_acceptance_artifact(tmp_path / "acceptance")
    request = _write_active_ready_request(tmp_path / "active_ready_request.json", acceptance, {"cache_mutated": True})
    settings = _happy_settings(tmp_path, acceptance, active_ready_request_manifest=request)

    result = run_active_replay_input_active_ready(settings)

    assert result.status == "ACTIVE_READY_SIDE_EFFECT_BLOCKED"
    assert result.cache_mutated is False
    assert result.ready_for_final_review is False


def test_authority_not_accepted_blocks(tmp_path: Path) -> None:
    acceptance = _write_acceptance_artifact(tmp_path / "acceptance")
    authority = _write_authority(tmp_path / "authority.json", {"authority_result": "REJECTED"})
    settings = _happy_settings(tmp_path, acceptance, active_ready_authority_manifest=authority)

    result = run_active_replay_input_active_ready(settings)

    assert result.status == "ACTIVE_READY_AUTHORITY_BLOCKED"
    assert result.ready_for_final_review is False


@pytest.mark.parametrize(
    ("manifest_name", "override", "expected_status"),
    [
        ("pit_coverage_manifest", {"available_time_coverage_complete": False}, "ACTIVE_READY_PIT_BLOCKED"),
        ("source_coverage_manifest", {"source_hash_coverage_complete": False}, "ACTIVE_READY_SOURCE_BLOCKED"),
        ("evidence_coverage_manifest", {"raw_evidence_refs_complete": False}, "ACTIVE_READY_EVIDENCE_BLOCKED"),
        ("taxonomy_compliance_manifest", {"not_fixed_12_only": False}, "ACTIVE_READY_TAXONOMY_BLOCKED"),
        ("leakage_review_manifest", {"no_future_labels": False}, "ACTIVE_READY_LEAKAGE_BLOCKED"),
        ("side_effect_review_manifest", {"no_snapshot_built": False}, "ACTIVE_READY_SIDE_EFFECT_BLOCKED"),
        ("overclaim_review_manifest", {"acceptance_not_active_ready": False}, "ACTIVE_READY_REVIEW_BLOCKED"),
    ],
)
def test_manifest_gate_failures_block_by_gate_group(
    tmp_path: Path, manifest_name: str, override: dict[str, object], expected_status: str
) -> None:
    acceptance = _write_acceptance_artifact(tmp_path / "acceptance")
    settings = _happy_settings(tmp_path, acceptance)
    replacement = _manifest_writer(manifest_name)(tmp_path / f"{manifest_name}.json", override)
    settings = ActiveReplayInputActiveReadySettings(
        output_dir=settings.output_dir,
        acceptance_artifact=settings.acceptance_artifact,
        acceptance_health_artifact=settings.acceptance_health_artifact,
        acceptance_status_artifact=settings.acceptance_status_artifact,
        active_ready_request_manifest=settings.active_ready_request_manifest,
        active_ready_authority_manifest=settings.active_ready_authority_manifest,
        pit_coverage_manifest=replacement if manifest_name == "pit_coverage_manifest" else settings.pit_coverage_manifest,
        source_coverage_manifest=replacement
        if manifest_name == "source_coverage_manifest"
        else settings.source_coverage_manifest,
        evidence_coverage_manifest=replacement
        if manifest_name == "evidence_coverage_manifest"
        else settings.evidence_coverage_manifest,
        taxonomy_compliance_manifest=replacement
        if manifest_name == "taxonomy_compliance_manifest"
        else settings.taxonomy_compliance_manifest,
        leakage_review_manifest=replacement
        if manifest_name == "leakage_review_manifest"
        else settings.leakage_review_manifest,
        side_effect_review_manifest=replacement
        if manifest_name == "side_effect_review_manifest"
        else settings.side_effect_review_manifest,
        overclaim_review_manifest=replacement
        if manifest_name == "overclaim_review_manifest"
        else settings.overclaim_review_manifest,
    )

    result = run_active_replay_input_active_ready(settings)

    assert result.status == expected_status
    assert result.ready_for_final_review is False
    assert result.active_replay_input_ready is False


def test_happy_path_returns_final_review_ready_only(tmp_path: Path) -> None:
    acceptance = _write_acceptance_artifact(tmp_path / "acceptance")

    result = run_active_replay_input_active_ready(_happy_settings(tmp_path, acceptance))

    assert result.status == ACTIVE_READY_READY_FOR_FINAL_REVIEW
    assert result.ready_for_final_review is True
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.active_ready_emitted is False
    assert result.forward_labels_exist is False
    assert result.weights_trained is False
    assert result.active_stock_profile_exists is False
    assert result.real_buy_review_eligible is False
    assert result.approval_applied is False
    assert result.overclaim_guard_pass_count == result.overclaim_guard_total_count
    assert result.artifact_path.is_relative_to(_active_ready_output_dir(tmp_path))
    assert "ACTIVE_REPLAY_INPUT_READY" not in result.status

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == ACTIVE_READY_READY_FOR_FINAL_REVIEW
    assert metadata["ready_for_final_review"] is True
    assert metadata["active_replay_input_ready"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["active_ready_emitted"] is False
    assert "ACTIVE_REPLAY_INPUT_READY" not in json.dumps(metadata)

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_cli_command_runs_without_active_ready_claim(tmp_path: Path) -> None:
    acceptance = _write_acceptance_artifact(tmp_path / "acceptance")
    settings = _happy_settings(tmp_path, acceptance)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "active-replay-input-active-ready",
            "--acceptance-artifact",
            str(settings.acceptance_artifact),
            "--acceptance-health-artifact",
            str(settings.acceptance_health_artifact),
            "--acceptance-status-artifact",
            str(settings.acceptance_status_artifact),
            "--active-ready-request-manifest",
            str(settings.active_ready_request_manifest),
            "--active-ready-authority-manifest",
            str(settings.active_ready_authority_manifest),
            "--pit-coverage-manifest",
            str(settings.pit_coverage_manifest),
            "--source-coverage-manifest",
            str(settings.source_coverage_manifest),
            "--evidence-coverage-manifest",
            str(settings.evidence_coverage_manifest),
            "--taxonomy-compliance-manifest",
            str(settings.taxonomy_compliance_manifest),
            "--leakage-review-manifest",
            str(settings.leakage_review_manifest),
            "--side-effect-review-manifest",
            str(settings.side_effect_review_manifest),
            "--overclaim-review-manifest",
            str(settings.overclaim_review_manifest),
            "--output-dir",
            str(_active_ready_output_dir(tmp_path)),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert "active_ready_run_id:" in completed.stdout
    assert f"status: {ACTIVE_READY_READY_FOR_FINAL_REVIEW}" in completed.stdout
    assert "ready_for_final_review: True" in completed.stdout
    assert "active_replay_input_ready: False" in completed.stdout
    assert "active_replay_input: False" in completed.stdout
    assert "active_ready_emitted: False" in completed.stdout
    assert "ACTIVE_REPLAY_INPUT_READY" not in completed.stdout

    help_text = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout
    assert "active-replay-input-active-ready" in help_text
    assert not Path("docs/project_sources").exists()


def test_no_input_cli_writes_artifacts_without_active_ready(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "active-replay-input-active-ready",
            "--output-dir",
            str(_active_ready_output_dir(tmp_path)),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert f"status: {NO_ACTIVE_READY_INPUT}" in completed.stdout
    assert "active_replay_input_ready: False" in completed.stdout
    assert "active_replay_input: False" in completed.stdout
    assert "active_ready_emitted: False" in completed.stdout
    assert "ACTIVE_REPLAY_INPUT_READY" not in completed.stdout


def test_index_discovers_no_input_and_final_review_ready_artifacts(tmp_path: Path) -> None:
    root = _active_ready_output_dir(tmp_path)
    no_input = run_active_replay_input_active_ready(ActiveReplayInputActiveReadySettings(output_dir=root))
    ready = _run_ready_active_ready(tmp_path, root)

    result = build_active_replay_input_active_ready_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 2
    assert set(result.index_frame["active_ready_run_id"]) == {
        no_input.active_ready_run_id,
        ready.active_ready_run_id,
    }
    ready_row = result.index_frame[result.index_frame["active_ready_run_id"] == ready.active_ready_run_id].iloc[0]
    assert ready_row["status"] == ACTIVE_READY_READY_FOR_FINAL_REVIEW
    assert ready_row["ready_for_final_review"] is True
    assert ready_row["active_replay_input_ready"] is False
    assert ready_row["active_replay_input"] is False
    assert ready_row["active_ready_emitted"] is False
    assert ready_row["forward_labels_exist"] is False
    assert ready_row["weights_trained"] is False
    assert ready_row["active_stock_profile_exists"] is False
    assert ready_row["real_buy_review_eligible"] is False
    assert ready_row["data_raw_written"] is False
    assert ready_row["data_processed_written"] is False
    assert ready_row["data_cache_written"] is False
    assert ready_row["report_only"] is True
    assert ready_row["diagnostic_only"] is True
    assert ready_row["overclaim_guard_pass_count"] == ready_row["overclaim_guard_total_count"]
    assert result.artifact_paths["index_csv"].exists()


def test_health_passes_for_valid_no_input_and_final_review_ready_artifacts(tmp_path: Path) -> None:
    root = _active_ready_output_dir(tmp_path)
    run_active_replay_input_active_ready(ActiveReplayInputActiveReadySettings(output_dir=root))
    no_input_health = check_active_replay_input_active_ready_health(root=root, output_dir=root / "health_no_input")
    assert no_input_health.status == "PASS"
    assert no_input_health.error_count == 0

    _run_ready_active_ready(tmp_path, root)
    ready_health = check_active_replay_input_active_ready_health(root=root, output_dir=root / "health_ready")
    assert ready_health.status == "PASS"
    assert ready_health.error_count == 0


@pytest.mark.parametrize(
    ("metadata_field", "metadata_value", "issue_code"),
    [
        ("status", "ACTIVE_REPLAY_INPUT_READY", "ACTIVE_REPLAY_INPUT_READY_UNEXPECTED"),
        ("active_ready_emitted", True, "ACTIVE_READY_EMITTED_UNEXPECTED"),
        ("active_replay_input_ready", True, "ACTIVE_REPLAY_INPUT_READY_UNEXPECTED"),
        ("active_replay_input", True, "ACTIVE_REPLAY_INPUT_UNEXPECTED"),
        ("forward_labels_exist", True, "FORWARD_LABELS_EXIST_UNEXPECTED"),
        ("weights_trained", True, "WEIGHTS_TRAINED_UNEXPECTED"),
        ("active_stock_profile_exists", True, "ACTIVE_STOCK_PROFILE_EXISTS_UNEXPECTED"),
        ("real_buy_review_eligible", True, "REAL_BUY_REVIEW_ELIGIBLE_UNEXPECTED"),
        ("order_placed", True, "ORDER_PLACED_UNEXPECTED"),
        ("message_sent", True, "MESSAGE_SENT_UNEXPECTED"),
        ("cache_mutated", True, "CACHE_MUTATED_UNEXPECTED"),
        ("data_raw_written", True, "DATA_RAW_WRITTEN_UNEXPECTED"),
        ("data_processed_written", True, "DATA_PROCESSED_WRITTEN_UNEXPECTED"),
        ("data_cache_written", True, "DATA_CACHE_WRITTEN_UNEXPECTED"),
    ],
)
def test_health_fails_for_unsafe_active_ready_metadata(
    tmp_path: Path, metadata_field: str, metadata_value: object, issue_code: str
) -> None:
    root = _active_ready_output_dir(tmp_path)
    active_ready = _run_ready_active_ready(tmp_path, root)
    _mutate_json(active_ready.artifact_paths["metadata"], {metadata_field: metadata_value})

    result = check_active_replay_input_active_ready_health(root=root, output_dir=root / "health")

    assert result.status == "FAIL"
    assert issue_code in set(result.health_frame["issue_code"])


def test_health_fails_when_overclaim_guards_fail(tmp_path: Path) -> None:
    root = _active_ready_output_dir(tmp_path)
    active_ready = _run_ready_active_ready(tmp_path, root)
    guards = pd.read_csv(active_ready.artifact_paths["overclaim_guard_report"], dtype=str)
    guards.loc[0, "passed"] = "False"
    guards.to_csv(active_ready.artifact_paths["overclaim_guard_report"], index=False)
    _mutate_json(active_ready.artifact_paths["metadata"], {"overclaim_guard_pass_count": 3})

    result = check_active_replay_input_active_ready_health(root=root, output_dir=root / "health")

    assert result.status == "FAIL"
    assert "OVERCLAIM_GUARD_FAILED" in set(result.health_frame["issue_code"])


def test_status_reports_final_review_ready_without_active_ready_claim(tmp_path: Path) -> None:
    root = _active_ready_output_dir(tmp_path)
    active_ready = _run_ready_active_ready(tmp_path, root)

    result = run_active_replay_input_active_ready_status(root=root, output_dir=root / "status")

    assert result.latest_active_ready_run_id == active_ready.active_ready_run_id
    assert result.status == ACTIVE_READY_READY_FOR_FINAL_REVIEW
    assert result.health_status == "PASS"
    assert result.workflow_stage == ACTIVE_READY_READY_FOR_FINAL_REVIEW
    assert result.ready_for_final_review is True
    assert result.active_replay_input_ready is False
    assert result.active_replay_input is False
    assert result.active_ready_emitted is False
    assert "report-only" in result.safety_statement
    assert "not ACTIVE_REPLAY_INPUT_READY" in result.safety_statement
    assert "does not create active replay input" in result.safety_statement
    assert "does not run replay" in result.safety_statement
    assert "does not compute forward labels" in result.safety_statement
    assert "does not train weights" in result.safety_statement
    assert "does not create active stock profiles" in result.safety_statement
    assert "does not create real buy-review eligibility" in result.safety_statement
    assert "does not authorize trading" in result.safety_statement


def test_status_reports_no_input_and_health_failed_stages(tmp_path: Path) -> None:
    root = _active_ready_output_dir(tmp_path)
    no_input = run_active_replay_input_active_ready(ActiveReplayInputActiveReadySettings(output_dir=root))
    no_input_status = run_active_replay_input_active_ready_status(root=root, output_dir=root / "status_no_input")
    assert no_input_status.latest_active_ready_run_id == no_input.active_ready_run_id
    assert no_input_status.workflow_stage == ACTIVE_READY_NO_INPUT

    _mutate_json(no_input.artifact_paths["metadata"], {"active_ready_emitted": True})
    failed_status = run_active_replay_input_active_ready_status(root=root, output_dir=root / "status_failed")
    assert failed_status.workflow_stage == ACTIVE_READY_HEALTH_FAILED
    assert failed_status.health_status == "FAIL"


def test_artifact_view_cli_commands_remain_report_only_with_research_status_context(tmp_path: Path) -> None:
    root = _active_ready_output_dir(tmp_path)
    active_ready = _run_ready_active_ready(tmp_path, root)

    commands = [
        ("active-replay-input-active-ready-index", "artifact_count: 1"),
        ("active-replay-input-active-ready-health", "status: PASS"),
        ("active-replay-input-active-ready-status", f"workflow_stage: {ACTIVE_READY_READY_FOR_FINAL_REVIEW}"),
    ]
    for command, expected_text in commands:
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
        assert expected_text in completed.stdout
        assert "No active replay input" in completed.stdout
        assert "ACTIVE_REPLAY_INPUT_READY" not in completed.stdout

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "research-status",
            "--root",
            str(tmp_path / "outputs" / "reports"),
            "--output-dir",
            str(tmp_path / "dashboard"),
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    assert active_ready.active_ready_run_id in completed.stdout
    assert "latest_active_replay_input_active_ready_run_id" in completed.stdout
    assert f"latest_active_replay_input_active_ready_workflow_stage: {ACTIVE_READY_READY_FOR_FINAL_REVIEW}" in completed.stdout
    assert "active_replay_input_ready: False" in completed.stdout
    assert "active_replay_input: False" in completed.stdout
    assert "active_ready_emitted: False" in completed.stdout
    assert "ACTIVE_REPLAY_INPUT_READY" not in completed.stdout
    assert not Path("docs/project_sources").exists()


def _active_ready_output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "active_replay_input_active_ready_v0_1"


def _run_ready_active_ready(tmp_path: Path, output_dir: Path):
    acceptance = _write_acceptance_artifact(tmp_path / "acceptance")
    settings = _happy_settings(tmp_path, acceptance)
    settings = ActiveReplayInputActiveReadySettings(
        output_dir=output_dir,
        acceptance_artifact=settings.acceptance_artifact,
        acceptance_health_artifact=settings.acceptance_health_artifact,
        acceptance_status_artifact=settings.acceptance_status_artifact,
        active_ready_request_manifest=settings.active_ready_request_manifest,
        active_ready_authority_manifest=settings.active_ready_authority_manifest,
        pit_coverage_manifest=settings.pit_coverage_manifest,
        source_coverage_manifest=settings.source_coverage_manifest,
        evidence_coverage_manifest=settings.evidence_coverage_manifest,
        taxonomy_compliance_manifest=settings.taxonomy_compliance_manifest,
        leakage_review_manifest=settings.leakage_review_manifest,
        side_effect_review_manifest=settings.side_effect_review_manifest,
        overclaim_review_manifest=settings.overclaim_review_manifest,
    )
    return run_active_replay_input_active_ready(settings)


def _required_artifact_keys() -> list[str]:
    return [
        "metadata",
        "active_ready_report",
        "active_ready_precondition_results",
        "authority_review_results",
        "acceptance_lineage_results",
        "pit_coverage_results",
        "source_coverage_results",
        "evidence_coverage_results",
        "taxonomy_compliance_results",
        "leakage_guard_results",
        "side_effect_guard_results",
        "overclaim_guard_report",
        "recommended_next_task",
    ]


def _happy_settings(
    tmp_path: Path,
    acceptance: Path,
    **overrides: Path | None,
) -> ActiveReplayInputActiveReadySettings:
    def default_path(name: str, writer):
        return overrides[name] if name in overrides else writer()

    values = {
        "output_dir": _active_ready_output_dir(tmp_path),
        "acceptance_artifact": acceptance,
        "acceptance_health_artifact": default_path(
            "acceptance_health_artifact",
            lambda: _write_json(tmp_path / "acceptance_health.json", {"health_status": "PASS"}),
        ),
        "acceptance_status_artifact": default_path(
            "acceptance_status_artifact",
            lambda: _write_json(
                tmp_path / "acceptance_status.json",
                {
                    "status": "ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW",
                    "ready_for_active_ready_review": True,
                    "active_replay_input_ready": False,
                    "active_replay_input": False,
                    "active_ready_emitted": False,
                },
            ),
        ),
        "active_ready_request_manifest": default_path(
            "active_ready_request_manifest",
            lambda: _write_active_ready_request(tmp_path / "active_ready_request.json", acceptance),
        ),
        "active_ready_authority_manifest": default_path(
            "active_ready_authority_manifest",
            lambda: _write_authority(tmp_path / "authority.json"),
        ),
        "pit_coverage_manifest": default_path(
            "pit_coverage_manifest",
            lambda: _write_pit_coverage(tmp_path / "pit_coverage.json"),
        ),
        "source_coverage_manifest": default_path(
            "source_coverage_manifest",
            lambda: _write_source_coverage(tmp_path / "source_coverage.json"),
        ),
        "evidence_coverage_manifest": default_path(
            "evidence_coverage_manifest",
            lambda: _write_evidence_coverage(tmp_path / "evidence_coverage.json"),
        ),
        "taxonomy_compliance_manifest": default_path(
            "taxonomy_compliance_manifest",
            lambda: _write_taxonomy(tmp_path / "taxonomy.json"),
        ),
        "leakage_review_manifest": default_path(
            "leakage_review_manifest",
            lambda: _write_leakage_review(tmp_path / "leakage.json"),
        ),
        "side_effect_review_manifest": default_path(
            "side_effect_review_manifest",
            lambda: _write_side_effect_review(tmp_path / "side_effect.json"),
        ),
        "overclaim_review_manifest": default_path(
            "overclaim_review_manifest",
            lambda: _write_overclaim_review(tmp_path / "overclaim.json"),
        ),
    }
    values.update(overrides)
    return ActiveReplayInputActiveReadySettings(**values)


def _write_acceptance_artifact(path: Path, overrides: dict[str, object] | None = None) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    metadata = {
        "acceptance_run_id": "acceptance_001",
        "status": "ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW",
        "workflow_stage": "ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW",
        "ready_for_active_ready_review": True,
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "active_ready_emitted": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
        "approval_applied": False,
        "order_placed": False,
        "message_sent": False,
        "llm_api_called": False,
        "external_api_called": False,
        "cache_mutated": False,
        "data_raw_written": False,
        "data_processed_written": False,
        "data_cache_written": False,
        "current_candidates_run": False,
        "snapshot_built": False,
        "signal_semantics_changed": False,
        "report_only": True,
        "diagnostic_only": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "artifact_path": str(path),
    }
    metadata.update(overrides or {})
    (path / "acceptance_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_active_ready_request(
    path: Path, acceptance: Path, overrides: dict[str, object] | None = None
) -> Path:
    payload = {
        "active_ready_request_id": "active_ready_request_001",
        "requested_by": "fixture_reviewer",
        "requested_at": "2024-04-02T18:00:00+08:00",
        "request_reason": "fixture final-review-only active-ready governance",
        "acceptance_artifact_ref": str(acceptance),
        "requested_status": "ACTIVE_READY_READY_FOR_FINAL_REVIEW",
        "report_only": True,
        "diagnostic_only": True,
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "active_ready_emitted": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
        "approval_applied": False,
        "order_placed": False,
        "message_sent": False,
        "llm_api_called": False,
        "external_api_called": False,
        "cache_mutated": False,
        "data_raw_written": False,
        "data_processed_written": False,
        "data_cache_written": False,
        "current_candidates_run": False,
        "snapshot_built": False,
        "signal_semantics_changed": False,
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_authority(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "active_ready_authority_id": "authority_001",
        "primary_approver": "primary_fixture_reviewer",
        "second_approver": "second_fixture_reviewer",
        "pit_reviewer": "pit_fixture_reviewer",
        "source_reviewer": "source_fixture_reviewer",
        "evidence_reviewer": "evidence_fixture_reviewer",
        "risk_compliance_reviewer": "risk_fixture_reviewer",
        "strategy_owner": "strategy_fixture_owner",
        "authority_scope": "review-only final-review-ready active-ready governance",
        "authority_result": "ACCEPTED_FOR_REVIEW_ONLY",
        "report_only": True,
        "diagnostic_only": True,
        "notes": "fixture only",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_pit_coverage(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "pit_coverage_id": "pit_001",
        "available_time_coverage_complete": True,
        "universe_coverage_complete": True,
        "suspension_st_delist_coverage_complete": True,
        "corporate_action_policy_reviewed": True,
        "pit_result": "PASS",
        "report_only": True,
        "diagnostic_only": True,
        "notes": "fixture only",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_source_coverage(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "source_coverage_id": "source_001",
        "source_id_coverage_complete": True,
        "source_hash_coverage_complete": True,
        "revision_id_coverage_complete": True,
        "permission_class_coverage_complete": True,
        "quality_status_coverage_complete": True,
        "source_result": "PASS",
        "report_only": True,
        "diagnostic_only": True,
        "notes": "fixture only",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_evidence_coverage(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "evidence_coverage_id": "evidence_001",
        "raw_evidence_refs_complete": True,
        "replay_evidence_bundle_complete": True,
        "factor_definition_coverage_complete": True,
        "factor_observation_coverage_complete": True,
        "event_structured_coverage_complete": True,
        "company_exposure_coverage_complete": True,
        "evidence_result": "PASS",
        "report_only": True,
        "diagnostic_only": True,
        "notes": "fixture only",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_taxonomy(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "taxonomy_compliance_id": "taxonomy_001",
        "uses_8_layer_taxonomy": True,
        "not_fixed_12_only": True,
        "factor_layer_metadata_complete": True,
        "trade_usage_metadata_complete": True,
        "compliance_metadata_complete": True,
        "taxonomy_result": "PASS",
        "report_only": True,
        "diagnostic_only": True,
        "notes": "fixture only",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_leakage_review(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "leakage_review_id": "leakage_001",
        "no_future_labels": True,
        "no_forward_returns": True,
        "no_training_outputs": True,
        "no_model_weights": True,
        "no_stock_profile_artifacts": True,
        "no_buy_review_eligibility": True,
        "leakage_result": "PASS",
        "report_only": True,
        "diagnostic_only": True,
        "notes": "fixture only",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_side_effect_review(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "side_effect_review_id": "side_effect_001",
        "no_approval_applied": True,
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
        "no_signal_semantics_changed": True,
        "side_effect_result": "PASS",
        "report_only": True,
        "diagnostic_only": True,
        "notes": "fixture only",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _write_overclaim_review(path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload = {
        "overclaim_review_id": "overclaim_001",
        "pass_candidate_not_active_ready": True,
        "smoke_not_active_ready": True,
        "promotion_not_active_ready": True,
        "acceptance_not_active_ready": True,
        "final_review_not_active_ready": True,
        "active_ready_not_replay": True,
        "active_ready_not_labels": True,
        "active_ready_not_training": True,
        "active_ready_not_stock_profile": True,
        "active_ready_not_buy_review": True,
        "active_ready_not_trading": True,
        "active_ready_not_performance_validation": True,
        "overclaim_result": "PASS",
        "report_only": True,
        "diagnostic_only": True,
        "notes": "fixture only",
    }
    payload.update(overrides or {})
    return _write_json(path, payload)


def _manifest_writer(manifest_name: str):
    return {
        "pit_coverage_manifest": _write_pit_coverage,
        "source_coverage_manifest": _write_source_coverage,
        "evidence_coverage_manifest": _write_evidence_coverage,
        "taxonomy_compliance_manifest": _write_taxonomy,
        "leakage_review_manifest": _write_leakage_review,
        "side_effect_review_manifest": _write_side_effect_review,
        "overclaim_review_manifest": _write_overclaim_review,
    }[manifest_name]


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _mutate_json(path: Path, updates: dict[str, object]) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(updates)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
