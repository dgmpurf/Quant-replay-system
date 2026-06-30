from __future__ import annotations

from pathlib import Path

import pytest

from quant_replay_system import cli


COMMAND = "tiny-pit-real-reviewed-local-csv-package-candidate-metadata-reference-following"
INDEX_COMMAND = f"{COMMAND}-index"
HEALTH_COMMAND = f"{COMMAND}-health"
STATUS_COMMAND = f"{COMMAND}-status"


def _root(tmp_path: Path) -> Path:
    return (
        tmp_path
        / "outputs"
        / "reports"
        / "manual_diagnostics"
        / "tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following_v0_1"
    )


def _run_cli(args: list[str], capsys) -> str:
    code = cli.main(args)
    output = capsys.readouterr()
    assert code == 0, output.err
    assert output.err == ""
    return output.out


def test_metadata_reference_following_cli_commands_have_help_and_hide_real_input_args(capsys) -> None:
    forbidden_help_tokens = [
        "package_manifest_path",
        "allowed_manifest_roots",
        "package-root",
        "reviewed-csv",
        "csv-path",
        "package discovery",
    ]

    for command in [COMMAND, INDEX_COMMAND, HEALTH_COMMAND, STATUS_COMMAND]:
        with pytest.raises(SystemExit) as exc_info:
            cli.main([command, "--help"])
        output = capsys.readouterr()

        assert exc_info.value.code == 0
        assert command in output.out
        for token in forbidden_help_tokens:
            assert token not in output.out


def test_metadata_reference_following_core_cli_no_input_writes_only_tmp_path_outputs(
    tmp_path: Path,
    capsys,
) -> None:
    root = _root(tmp_path)

    output = _run_cli(
        [
            COMMAND,
            "--output-root",
            str(root),
            "--run-id",
            "cli_no_input",
        ],
        capsys,
    )

    assert "runtime_status: NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_INPUT" in output
    assert "csv_read_level: CSV_READ_NONE" in output
    assert "real_manifest_read: False" in output
    assert "references_declared: False" in output
    assert "references_followed: False" in output
    assert "metadata_files_followed_count: 0" in output
    assert "local_file_hash_computed: False" in output
    assert "external_source_validated: False" in output
    assert "pit_admissibility_validated: False" in output
    assert "real_csv_consumed: False" in output
    assert "real_reviewed_csv_package_created: False" in output
    assert "real_package_candidate_created: False" in output
    assert "active_reviewed_input_candidate_created: False" in output
    assert "real_replay_input_created: False" in output
    assert "active_replay_input: False" in output
    assert "active_replay_ready: False" in output
    assert "active_replay_input_ready_emitted: False" in output
    assert "replay_execution_allowed: False" in output
    assert "trading_allowed: False" in output
    assert "buy_review_allowed: False" in output
    assert "data_raw_written: False" in output
    assert "data_processed_written: False" in output
    assert "data_cache_written: False" in output
    assert "artifact_path:" in output
    assert "report_path:" in output
    assert "recommended_next_task:" in output
    assert "metadata-only local JSON references" in output
    assert "CSV/data references" in output
    _assert_no_forbidden_wording(output)
    _assert_no_protected_dirs(tmp_path)
    assert (root / "cli_no_input" / "metadata.json").is_file()


def test_metadata_reference_following_index_health_status_cli_commands_use_tmp_path(
    tmp_path: Path,
    capsys,
) -> None:
    root = _root(tmp_path)
    _run_cli([COMMAND, "--output-root", str(root), "--run-id", "cli_no_input"], capsys)

    index_output = _run_cli([INDEX_COMMAND, "--root", str(root), "--output-dir", str(root / "index")], capsys)
    assert "latest_runtime_status: NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_INPUT" in index_output
    assert "artifact_count: 1" in index_output
    _assert_no_forbidden_wording(index_output)

    health_output = _run_cli([HEALTH_COMMAND, "--root", str(root), "--output-dir", str(root / "health")], capsys)
    assert "health_status: PASS" in health_output
    assert "issue_count: 0" in health_output
    _assert_no_forbidden_wording(health_output)

    status_output = _run_cli([STATUS_COMMAND, "--root", str(root), "--output-dir", str(root / "status")], capsys)
    assert "latest_runtime_status: NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_METADATA_REFERENCE_INPUT" in status_output
    assert "latest_health_status: PASS" in status_output
    assert "csv_read_level: CSV_READ_NONE" in status_output
    assert "recommended_next_task:" in status_output
    assert "references_followed: False" in status_output
    assert "metadata-only local JSON references" in status_output
    assert "CSV/data references" in status_output
    _assert_no_forbidden_wording(status_output)
    _assert_no_protected_dirs(tmp_path)


def test_metadata_reference_following_cli_does_not_create_docs_project_sources(tmp_path: Path, capsys) -> None:
    root = _root(tmp_path)

    _run_cli([COMMAND, "--output-root", str(root)], capsys)

    assert not Path("docs/project_sources").exists()
    _assert_no_protected_dirs(tmp_path)


def _assert_no_forbidden_wording(output: str) -> None:
    for token in [
        "ACTIVE_REPLAY_INPUT_READY",
        "READY_FOR_REPLAY",
        "TRADING_READY",
        "BUY_REVIEW_READY",
        "PACKAGE_APPROVED",
        "PACKAGE_ADMISSIBLE",
        "PERFORMANCE_VALIDATED",
    ]:
        assert token not in output


def _assert_no_protected_dirs(tmp_path: Path) -> None:
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()
