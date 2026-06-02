import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.point_in_time_universe_export_staging_health import (
    check_pit_universe_export_staging_health,
)
from quant_replay_system.point_in_time_universe_export_staging_index import (
    build_pit_universe_export_staging_index,
)
from quant_replay_system.point_in_time_universe_export_staging import STAGING_OUTPUT_COLUMNS
from quant_replay_system.point_in_time_universe_export_staging_status import (
    run_pit_universe_export_staging_status,
)


def test_index_detects_staging_artifacts(tmp_path: Path) -> None:
    _write_staging_artifact(tmp_path / "staging" / "stage-a", staging_id="stage-a")

    result = build_pit_universe_export_staging_index(root=tmp_path / "staging", output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0].to_dict()
    assert row["staging_id"] == "stage-a"
    assert row["export_readiness_id"] == "readiness-a"
    assert row["no_ready_rows"] is True
    assert row["would_write_data_raw"] is False
    assert row["would_write_data_processed"] is False


def test_health_warn_or_pass_for_no_ready_blocked_staging(tmp_path: Path) -> None:
    _write_staging_artifact(tmp_path / "staging" / "stage-a", staging_id="stage-a")

    result = check_pit_universe_export_staging_health(root=tmp_path / "staging", output_dir=tmp_path / "health")

    assert result.status in {"PASS", "WARN"}
    assert result.error_count == 0
    assert result.checked_artifact_count == 1


def test_health_fails_if_data_raw_or_processed_write_occurred(tmp_path: Path) -> None:
    _write_staging_artifact(
        tmp_path / "staging" / "stage-a",
        staging_id="stage-a",
        metadata_overrides={"would_write_data_raw": True, "would_write_data_processed": True},
    )

    result = check_pit_universe_export_staging_health(root=tmp_path / "staging", output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert {"DATA_RAW_WRITE_DETECTED", "DATA_PROCESSED_WRITE_DETECTED"} <= set(result.health_frame["issue_code"])


def test_health_fails_if_current_candidates_generated(tmp_path: Path) -> None:
    _write_staging_artifact(
        tmp_path / "staging" / "stage-a",
        staging_id="stage-a",
        metadata_overrides={"current_candidates_executed": True},
    )

    result = check_pit_universe_export_staging_health(root=tmp_path / "staging", output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "CURRENT_CANDIDATES_GENERATED" in set(result.health_frame["issue_code"])


def test_status_summarizes_latest_staging(tmp_path: Path) -> None:
    _write_staging_artifact(tmp_path / "staging" / "stage-a", staging_id="stage-a")

    result = run_pit_universe_export_staging_status(root=tmp_path / "staging", output_dir=tmp_path / "status")

    assert result.latest_staging_id == "stage-a"
    assert result.status == "WARN"
    assert result.workflow_stage == "PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS"
    assert result.health_status in {"PASS", "WARN"}
    assert result.export_readiness_id == "readiness-a"
    assert result.staged_row_count == 0
    assert result.blocked_count == 1
    assert result.no_ready_rows is True


def test_cli_index_health_status_work(tmp_path: Path, capsys) -> None:
    _write_staging_artifact(tmp_path / "staging" / "stage-a", staging_id="stage-a")

    index_code = cli.main(
        [
            "pit-universe-export-staging-index",
            "--root",
            str(tmp_path / "staging"),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    health_code = cli.main(
        [
            "pit-universe-export-staging-health",
            "--root",
            str(tmp_path / "staging"),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    status_code = cli.main(
        [
            "pit-universe-export-staging-status",
            "--root",
            str(tmp_path / "staging"),
            "--output-dir",
            str(tmp_path / "status"),
        ]
    )

    output = capsys.readouterr().out
    assert index_code == 0
    assert health_code == 0
    assert status_code == 0
    assert "artifact_count: 1" in output
    assert "latest_staging_id: stage-a" in output
    assert "workflow_stage: PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS" in output
    assert "No data/raw write, data/processed write" in output


def _write_staging_artifact(
    artifact_dir: Path,
    *,
    staging_id: str,
    metadata_overrides: dict | None = None,
) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    staging_csv = artifact_dir / "pit_universe_export_staging.csv"
    report = artifact_dir / "pit_universe_export_staging_report.md"
    row = {column: "" for column in STAGING_OUTPUT_COLUMNS}
    row.update({
        "staging_id": staging_id,
        "export_readiness_id": "readiness-a",
        "review_id": "review-a",
        "signal_date": "2024-04-02",
        "symbol": "000001",
        "universe_name": "etf_core",
        "export_ready": False,
        "staging_status": "EXPORT_STAGING_BLOCKED_NO_READY_ROWS",
        "staging_blocker_reason": "No export-ready PIT universe rows are available.",
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "staging_only": True,
        "source_is_diagnostic": False,
    })
    pd.DataFrame([row]).to_csv(staging_csv, index=False)
    report.write_text("# PIT Universe Export Staging\n", encoding="utf-8")
    metadata = {
        "staging_id": staging_id,
        "status": "WARN",
        "staging_status": "EXPORT_STAGING_BLOCKED_NO_READY_ROWS",
        "export_readiness_id": "readiness-a",
        "review_id": "review-a",
        "row_count": 1,
        "export_ready_input_count": 0,
        "staged_row_count": 0,
        "blocked_count": 1,
        "source_is_diagnostic": False,
        "no_ready_rows": True,
        "duplicate_key_count": 0,
        "missing_required_columns_count": 0,
        "would_write_data_raw": False,
        "would_write_data_processed": False,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "staging_only": True,
        "output_files": {
            "staging_csv": str(staging_csv),
            "report": str(report),
            "metadata": str(artifact_dir / "metadata.json"),
        },
    }
    metadata.update(metadata_overrides or {})
    (artifact_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return staging_csv
