from __future__ import annotations

import json
from pathlib import Path

from quant_replay_system import cli


COMMAND = "historical-replay-official-source-hierarchy-and-evidence-collection-worklist"
INDEX_COMMAND = f"{COMMAND}-index"
HEALTH_COMMAND = f"{COMMAND}-health"
STATUS_COMMAND = f"{COMMAND}-status"
NEXT_TASK = (
    "Historical Replay Official Manual Evidence Collection Template Design Report-Only v0.1"
)
STALE_NEXT_TASK_PHRASES = [
    "Historical Replay Official Source Hierarchy and Evidence Collection Worklist "
    "Artifact Views / Status Report-Only v0.1",
    "Historical Replay Official Source Hierarchy and Evidence Collection Worklist "
    "CLI Report-Only v0.1",
    "Historical Replay Official Source Hierarchy and Evidence Collection Worklist "
    "Research-Status Integration Planning Report-Only v0.1",
    "Historical Replay Official Source Hierarchy and Evidence Collection Worklist "
    "Checkpoint Planning Report-Only v0.1",
]


def test_cli_command_registration_for_all_four_commands() -> None:
    help_text = cli.build_parser().format_help()

    for command in [COMMAND, INDEX_COMMAND, HEALTH_COMMAND, STATUS_COMMAND]:
        assert command in help_text


def test_core_cli_help_contains_safe_args_and_no_forbidden_execution_flags(capsys) -> None:
    try:
        cli.build_parser().parse_args([COMMAND, "--help"])
    except SystemExit as exc:
        assert exc.code == 0
    output = capsys.readouterr().out

    for allowed in ["--root", "--output-dir", "--run-id", "--historical-decision-date", "--universe-name"]:
        assert allowed in output
    for forbidden in [
        "--collect-official-evidence",
        "--approve-official-source",
        "--close-evidence",
        "--approve-pit",
        "--pit-admissible",
        "--active-replay-input",
        "--run-replay",
        "--freeze-decision",
        "--create-labels",
        "--compute-metrics",
        "--train",
        "--model",
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


def test_core_cli_writes_expected_files_and_prints_counts_and_safety(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "worklist"

    exit_code = cli.main(
        [
            COMMAND,
            "--root",
            str(tmp_path / "repo"),
            "--output-dir",
            str(output_dir),
            "--run-id",
            "cli_core",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "worklist_run_id: cli_core" in output
    assert "historical_decision_date: 2024-04-02" in output
    assert "universe_name: etf_core" in output
    assert "row_count: 9" in output
    assert "stock_row_count: 7" in output
    assert "etf_row_count: 2" in output
    assert "source_class_count: 7" in output
    assert "evidence_family_count: 9" in output
    assert "evidence_collection_worklist_row_count: 72" in output
    assert "no_hit_handoff_row_count: 9" in output
    assert "blocked_count: 72" in output
    assert "profile_conflict_count: 7" in output
    assert "survivorship_warning_count: 9" in output
    assert f"recommended_next_task: {NEXT_TASK}" in output
    for stale_phrase in STALE_NEXT_TASK_PHRASES:
        assert stale_phrase not in output
    _assert_safety_statements(output)
    _assert_no_positive_readiness(output)
    for filename in [
        "metadata.json",
        "official_source_hierarchy_matrix.csv",
        "official_evidence_collection_worklist.csv",
        "official_evidence_family_requirement_matrix.csv",
        "official_source_lineage_requirement_matrix.csv",
        "official_no_hit_query_handoff_matrix.csv",
        "official_collection_blocker_matrix.csv",
        "official_collection_safety_flags.json",
        "official_source_hierarchy_and_evidence_collection_worklist_report.md",
    ]:
        assert (output_dir / "cli_core" / filename).exists()
    _assert_safety_flags_false(output_dir / "cli_core" / "official_collection_safety_flags.json")


def test_index_health_status_cli_wrap_existing_artifacts(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "worklist"
    assert cli.main([COMMAND, "--root", str(tmp_path / "repo"), "--output-dir", str(output_dir), "--run-id", "cli_core"]) == 0
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
    assert "row_count: 9" in index_output
    assert "evidence_collection_worklist_row_count: 72" in index_output
    assert "no_hit_handoff_row_count: 9" in index_output
    assert health_code == 0
    assert "health_status: OFFICIAL_SOURCE_HIERARCHY_WORKLIST_HEALTH_WARN_REVIEW_REQUIRED" in health_output
    assert status_code == 0
    assert "latest_run_id: cli_core" in status_output
    assert "latest_health_status: OFFICIAL_SOURCE_HIERARCHY_WORKLIST_HEALTH_WARN_REVIEW_REQUIRED" in status_output
    assert "row_count: 9" in status_output
    assert "evidence_collection_worklist_row_count: 72" in status_output
    assert "no_hit_handoff_row_count: 9" in status_output
    assert f"recommended_next_task: {NEXT_TASK}" in status_output
    for stale_phrase in STALE_NEXT_TASK_PHRASES:
        assert stale_phrase not in status_output
    for output in [index_output, health_output, status_output]:
        _assert_safety_statements(output)
        _assert_no_positive_readiness(output)


def test_health_cli_returns_nonzero_for_fail_only(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "worklist"
    assert cli.main([COMMAND, "--root", str(tmp_path / "repo"), "--output-dir", str(output_dir), "--run-id", "unsafe"]) == 0
    metadata_path = output_dir / "unsafe" / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["trading_allowed"] = True
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _ = capsys.readouterr()

    exit_code = cli.main([HEALTH_COMMAND, "--root", str(output_dir), "--output-dir", str(output_dir / "health")])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "health_status: OFFICIAL_SOURCE_HIERARCHY_WORKLIST_HEALTH_FAIL_UNSAFE" in output


def test_cli_commands_do_not_create_docs_project_sources_or_protected_data_dirs(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "worklist"

    assert cli.main([COMMAND, "--root", str(tmp_path / "repo"), "--output-dir", str(output_dir), "--run-id", "safe"]) == 0
    assert cli.main([INDEX_COMMAND, "--root", str(output_dir), "--output-dir", str(output_dir / "index")]) == 0
    assert cli.main([HEALTH_COMMAND, "--root", str(output_dir), "--output-dir", str(output_dir / "health")]) == 0
    assert cli.main([STATUS_COMMAND, "--root", str(output_dir), "--output-dir", str(output_dir / "status")]) == 0
    _ = capsys.readouterr()

    assert not (tmp_path / "docs" / "project_sources").exists()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_cli_output_does_not_expose_positive_readiness_wording(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "worklist"
    commands = [
        [COMMAND, "--root", str(tmp_path / "repo"), "--output-dir", str(output_dir), "--run-id", "safe"],
        [INDEX_COMMAND, "--root", str(output_dir), "--output-dir", str(output_dir / "index")],
        [HEALTH_COMMAND, "--root", str(output_dir), "--output-dir", str(output_dir / "health")],
        [STATUS_COMMAND, "--root", str(output_dir), "--output-dir", str(output_dir / "status")],
    ]

    for args in commands:
        assert cli.main(args) == 0
        _assert_no_positive_readiness(capsys.readouterr().out)


def test_cli_commands_do_not_expose_forbidden_approval_or_execution_flags() -> None:
    help_text = cli.build_parser().format_help()

    for forbidden in [
        "--approve-official-source",
        "--collect-official-evidence",
        "--close-evidence",
        "--approve-pit",
        "--pit-admissible",
        "--active-replay-input",
        "--run-replay",
        "--freeze-decision",
        "--create-labels",
        "--compute-metrics",
        "--write-data",
    ]:
        assert forbidden not in help_text


def _assert_safety_flags_false(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    for field in [
        "official_source_hierarchy_approved",
        "official_evidence_collection_approved",
        "official_status_evidence_closed",
        "pit_evidence_closed",
        "pit_admissibility_approved",
        "active_replay_input",
        "replay_execution_allowed",
        "replay_decision_freeze_allowed",
        "forward_labels_created",
        "metric_computation_performed",
        "model_training_performed",
        "stock_profile_validation_created",
        "buy_review_allowed",
        "trading_allowed",
        "broker_api_called",
        "order_placed",
        "message_sent",
        "data_raw_written",
        "data_processed_written",
        "data_cache_written",
    ]:
        assert payload[field] is False


def _assert_safety_statements(output: str) -> None:
    for expected in [
        "no official source hierarchy approval",
        "no official evidence collection approval",
        "no official status evidence closure",
        "no PIT evidence closure",
        "no PIT admissibility approval",
        "no active replay input",
        "no replay execution",
        "no decision freeze",
        "no forward labels",
        "no metric computation",
        "no training/model/stock_profile/paper expansion",
        "no buy-review",
        "no trading",
        "no broker API",
        "no orders",
        "no messages",
        "no external or LLM API",
        "no current-candidates",
        "no snapshots",
        "no signal semantics mutation",
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
