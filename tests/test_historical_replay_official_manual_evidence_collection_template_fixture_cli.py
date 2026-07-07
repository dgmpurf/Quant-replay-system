from __future__ import annotations

import json
from pathlib import Path

from quant_replay_system import cli


COMMAND = "historical-replay-official-manual-evidence-collection-template-fixture"
INDEX_COMMAND = f"{COMMAND}-index"
HEALTH_COMMAND = f"{COMMAND}-health"
STATUS_COMMAND = f"{COMMAND}-status"
NEXT_TASK = (
    "Historical Replay Official Manual Evidence Collection Template Generated Artifact Review Report-Only v0.1"
)


def test_cli_command_registration_for_all_four_commands() -> None:
    help_text = cli.build_parser().format_help()

    for command in [COMMAND, INDEX_COMMAND, HEALTH_COMMAND, STATUS_COMMAND]:
        assert command in help_text


def test_core_cli_help_contains_safe_args_and_no_collection_or_approval_flags(capsys) -> None:
    try:
        cli.build_parser().parse_args([COMMAND, "--help"])
    except SystemExit as exc:
        assert exc.code == 0
    output = capsys.readouterr().out

    for allowed in ["--root", "--output-dir", "--run-id", "--historical-decision-date", "--universe-name"]:
        assert allowed in output
    for forbidden in [
        "--collect-official-evidence",
        "--source-file",
        "--source-url",
        "--filled-evidence-path",
        "--approve-pit",
        "--pit-admissible",
        "--active-replay-input",
        "--run-replay",
        "--freeze-decision",
        "--create-labels",
        "--compute-metrics",
        "--train",
        "--stock-profile",
        "--paper",
        "--buy-review",
        "--trade",
        "--broker",
        "--order",
        "--message",
        "--write-data",
    ]:
        assert forbidden not in output


def test_core_cli_writes_template_artifacts_and_prints_counts_and_safety(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "template_fixture"

    exit_code = cli.main(
        [
            COMMAND,
            "--root",
            str(tmp_path / "reports"),
            "--output-dir",
            str(output_dir),
            "--run-id",
            "cli_core",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "template_fixture_run_id: cli_core" in output
    assert "row_count: 9" in output
    assert "stock_row_count: 7" in output
    assert "etf_row_count: 2" in output
    assert "evidence_collection_template_row_count: 72" in output
    assert "source_lineage_template_row_count: 72" in output
    assert "no_hit_template_row_count: 9" in output
    assert "survivorship_template_row_count: 9" in output
    assert "reviewer_notes_template_row_count: 9" in output
    assert "safety_true_count: 0" in output
    assert f"recommended_next_task: {NEXT_TASK}" in output
    _assert_safety_statement(output)
    _assert_no_positive_readiness(output)
    for filename in [
        "metadata.json",
        "official_evidence_collection_template.csv",
        "official_source_lineage_template.csv",
        "official_no_hit_query_handoff_template.csv",
        "official_survivorship_rationale_template.csv",
        "official_reviewer_notes_template.csv",
        "official_template_validation_checklist.md",
        "official_manual_evidence_collection_template_report.md",
        "official_manual_evidence_collection_template_safety_flags.json",
    ]:
        assert (output_dir / "cli_core" / filename).exists()


def test_index_health_status_cli_wrap_existing_template_artifacts(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "template_fixture"
    assert cli.main([COMMAND, "--root", str(tmp_path / "reports"), "--output-dir", str(output_dir), "--run-id", "cli_core"]) == 0
    _ = capsys.readouterr()

    index_code = cli.main([INDEX_COMMAND, "--root", str(output_dir), "--output-dir", str(output_dir / "index")])
    index_output = capsys.readouterr().out
    health_code = cli.main([HEALTH_COMMAND, "--root", str(output_dir), "--output-dir", str(output_dir / "health")])
    health_output = capsys.readouterr().out
    status_code = cli.main([STATUS_COMMAND, "--root", str(output_dir), "--output-dir", str(output_dir / "status")])
    status_output = capsys.readouterr().out

    assert index_code == 0
    assert "artifact_count: 1" in index_output
    assert "latest_run_id: cli_core" in index_output
    assert "evidence_collection_template_row_count: 72" in index_output
    assert health_code == 0
    assert "health_status: OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_HEALTH_PASS_REPORT_ONLY" in health_output
    assert status_code == 0
    assert "latest_run_id: cli_core" in status_output
    assert "latest_health_status: OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_HEALTH_PASS_REPORT_ONLY" in status_output
    assert "evidence_collection_template_row_count: 72" in status_output
    assert f"recommended_next_task: {NEXT_TASK}" in status_output
    for output in [index_output, health_output, status_output]:
        _assert_safety_statement(output)
        _assert_no_positive_readiness(output)


def test_health_cli_returns_nonzero_for_fail_only(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "template_fixture"
    assert cli.main([COMMAND, "--root", str(tmp_path / "reports"), "--output-dir", str(output_dir), "--run-id", "unsafe"]) == 0
    metadata_path = output_dir / "unsafe" / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["trading_allowed"] = True
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _ = capsys.readouterr()

    exit_code = cli.main([HEALTH_COMMAND, "--root", str(output_dir), "--output-dir", str(output_dir / "health")])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "health_status: OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_HEALTH_FAIL_UNSAFE" in output


def test_cli_commands_do_not_create_docs_project_sources_or_protected_data_dirs(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "template_fixture"

    assert cli.main([COMMAND, "--root", str(tmp_path / "reports"), "--output-dir", str(output_dir), "--run-id", "safe"]) == 0
    assert cli.main([INDEX_COMMAND, "--root", str(output_dir), "--output-dir", str(output_dir / "index")]) == 0
    assert cli.main([HEALTH_COMMAND, "--root", str(output_dir), "--output-dir", str(output_dir / "health")]) == 0
    assert cli.main([STATUS_COMMAND, "--root", str(output_dir), "--output-dir", str(output_dir / "status")]) == 0
    _ = capsys.readouterr()

    assert not (tmp_path / "docs" / "project_sources").exists()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def _assert_safety_statement(output: str) -> None:
    for expected in [
        "no official evidence collection",
        "no official evidence acceptance",
        "no PIT admissibility approval",
        "no active replay input",
        "no replay execution",
        "no buy-review",
        "no trading",
        "no protected data writes",
    ]:
        assert expected in output


def _assert_no_positive_readiness(output: str) -> None:
    for forbidden in [
        "PIT_ADMISSIBLE",
        "PIT_APPROVED",
        "READY_FOR_REPLAY",
        "ACTIVE_REPLAY_INPUT_READY",
        "BUY_REVIEW_READY",
        "TRADING_READY",
        "APPROVED_FOR_PAPER",
        "PERFORMANCE_VALIDATED",
    ]:
        assert forbidden not in output
