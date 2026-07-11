from __future__ import annotations

import json
from pathlib import Path

from quant_replay_system import cli


COMMAND = "historical-replay-source-evidence-sufficiency-policy-contract-fixture"
INDEX_COMMAND = f"{COMMAND}-index"
HEALTH_COMMAND = f"{COMMAND}-health"
STATUS_COMMAND = f"{COMMAND}-status"
NEXT_TASK = (
    "Historical Replay Source / Evidence Sufficiency Policy Contract Fixture "
    "Checkpoint Documentation Bundle Report-Only v0.1"
)
OLD_COMPLETED_REVIEW_TASK = (
    "Historical Replay Source / Evidence Sufficiency Policy Contract Fixture "
    "Generated Artifact Review Report-Only v0.1"
)
STALE_DESIGN_TASK = (
    "Historical Replay Source / Evidence Sufficiency Policy Contract Fixture "
    "Design Report-Only v0.1"
)


def test_cli_registers_exact_command_family() -> None:
    help_text = cli.build_parser().format_help()
    for command in [COMMAND, INDEX_COMMAND, HEALTH_COMMAND, STATUS_COMMAND]:
        assert command in help_text


def test_core_cli_help_contains_safe_arguments_only(capsys) -> None:
    try:
        cli.build_parser().parse_args([COMMAND, "--help"])
    except SystemExit as exc:
        assert exc.code == 0
    output = capsys.readouterr().out

    assert "--output-dir" in output
    assert "--run-id" in output
    for forbidden in [
        "--source-url",
        "--source-file",
        "--source-content",
        "--target-csv",
        "--evidence",
        "--accept",
        "--close",
        "--approve-pit",
        "--active-replay-input",
        "--run-replay",
        "--paper",
        "--buy-review",
        "--broker",
        "--order",
        "--message",
        "--trade",
    ]:
        assert forbidden not in output


def test_core_cli_creates_deterministic_contract_without_private_path_output(
    tmp_path: Path, capsys
) -> None:
    root = tmp_path / "fixture"
    exit_code = cli.main(
        [COMMAND, "--output-dir", str(root), "--run-id", "cli-fixture"]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "run_id: cli-fixture" in output
    for expected in [
        "row_count: 9",
        "stock_row_count: 7",
        "etf_row_count: 2",
        "evidence_family_count: 17",
        "row_evidence_family_contract_count: 153",
        "applicable_contract_row_count: 144",
        "instrument_not_applicable_context_row_count: 9",
        "selected_row_with_blocker_count: 9",
        "sufficiency_candidate_count: 0",
        "evidence_accepted_count: 0",
        "evidence_closed_count: 0",
        "pit_admissible_count: 0",
        "replay_ready_count: 0",
        "safety_true_count: 0",
        f"recommended_next_task: {NEXT_TASK}",
    ]:
        assert expected in output
    assert OLD_COMPLETED_REVIEW_TASK not in output
    assert STALE_DESIGN_TASK not in output
    assert str(tmp_path) not in output
    assert len(list((root / "cli-fixture").iterdir())) == 10


def test_index_health_and_status_cli_wrap_safe_fixture(tmp_path: Path, capsys) -> None:
    root = tmp_path / "fixture"
    assert cli.main([COMMAND, "--output-dir", str(root), "--run-id", "cli-fixture"]) == 0
    capsys.readouterr()

    assert cli.main([INDEX_COMMAND, "--root", str(root)]) == 0
    index_output = capsys.readouterr().out
    assert cli.main([HEALTH_COMMAND, "--root", str(root)]) == 0
    health_output = capsys.readouterr().out
    assert cli.main([STATUS_COMMAND, "--root", str(root)]) == 0
    status_output = capsys.readouterr().out

    assert "artifact_count: 1" in index_output
    assert "latest_run_id: cli-fixture" in index_output
    assert "report_reference: cli-fixture/" in index_output
    assert "health_status: SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_HEALTH_PASS_REPORT_ONLY" in health_output
    assert "checked_artifact_count: 1" in health_output
    assert "latest_run_id: cli-fixture" in status_output
    assert "latest_health_status: SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_HEALTH_PASS_REPORT_ONLY" in status_output
    assert f"recommended_next_task: {NEXT_TASK}" in status_output
    assert OLD_COMPLETED_REVIEW_TASK not in status_output
    for output in [index_output, health_output, status_output]:
        assert str(tmp_path) not in output
        assert "ACTIVE_REPLAY_INPUT_READY" not in output
        assert "TRADING_READY" not in output


def test_health_cli_returns_nonzero_for_unsafe_fixture(tmp_path: Path, capsys) -> None:
    root = tmp_path / "fixture"
    assert cli.main([COMMAND, "--output-dir", str(root), "--run-id", "unsafe"]) == 0
    metadata_path = root / "unsafe" / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["trading_allowed"] = True
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    capsys.readouterr()

    exit_code = cli.main([HEALTH_COMMAND, "--root", str(root)])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "health_status: SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_HEALTH_FAIL_UNSAFE" in output


def test_no_artifact_status_is_benign_and_zero_count(tmp_path: Path, capsys) -> None:
    root = tmp_path / "empty"
    root.mkdir()
    exit_code = cli.main([STATUS_COMMAND, "--root", str(root)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "status: SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_STATUS_NO_ARTIFACTS" in output
    assert "row_count: 0" in output
    assert "safety_true_count: 0" in output


def test_cli_family_creates_no_protected_data_or_project_source_paths(
    tmp_path: Path, capsys
) -> None:
    root = tmp_path / "fixture"
    assert cli.main([COMMAND, "--output-dir", str(root), "--run-id", "safe"]) == 0
    assert cli.main([INDEX_COMMAND, "--root", str(root)]) == 0
    assert cli.main([HEALTH_COMMAND, "--root", str(root)]) == 0
    assert cli.main([STATUS_COMMAND, "--root", str(root)]) == 0
    capsys.readouterr()

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()
