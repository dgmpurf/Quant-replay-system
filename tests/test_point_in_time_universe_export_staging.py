import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.point_in_time_universe_export_staging import (
    build_pit_universe_export_staging,
)


def test_no_ready_readiness_blocks_staging(tmp_path: Path) -> None:
    readiness = _write_readiness_artifact(tmp_path, [_blocked_readiness_row("000001")])

    result = build_pit_universe_export_staging(export_readiness=readiness, output_dir=tmp_path / "out")

    assert result.staging_status == "EXPORT_STAGING_BLOCKED_NO_READY_ROWS"
    assert result.row_count == 1
    assert result.export_ready_input_count == 0
    assert result.staged_row_count == 0
    assert result.blocked_count == 1
    assert result.no_ready_rows is True
    assert result.source_is_diagnostic is False
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["would_write_data_raw"] is False
    assert metadata["would_write_data_processed"] is False
    assert metadata["no_current_candidates_generated"] is True
    assert metadata["no_snapshot_built"] is True
    assert metadata["no_forward_labels"] is True


def test_diagnostic_export_ready_source_is_blocked_by_default(tmp_path: Path) -> None:
    readiness = _write_readiness_artifact(
        tmp_path / "outputs" / "reports" / "manual_diagnostics" / "diag_case",
        [_ready_readiness_row("000001")],
        review_rows=[_complete_review_row("000001")],
    )

    result = build_pit_universe_export_staging(export_readiness=readiness, output_dir=tmp_path / "out")

    assert result.source_is_diagnostic is True
    assert result.staging_status == "EXPORT_STAGING_BLOCKED_DIAGNOSTIC_SOURCE"
    assert result.export_ready_input_count == 1
    assert result.staged_row_count == 0
    assert result.blocked_count == 1


def test_diagnostic_source_can_be_used_only_for_isolated_outputs(tmp_path: Path) -> None:
    diagnostic_root = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "diag_case"
    readiness = _write_readiness_artifact(
        diagnostic_root,
        [_ready_readiness_row("000001")],
        review_rows=[_complete_review_row("000001")],
    )

    result = build_pit_universe_export_staging(
        export_readiness=readiness,
        output_dir=diagnostic_root / "staging",
        allow_diagnostic_source=True,
    )

    assert result.source_is_diagnostic is True
    assert result.staged_row_count == 1
    assert result.staging_status == "EXPORT_STAGING_DRY_RUN_CREATED"
    assert result.artifact_paths["combined_preview_csv"].exists()
    assert "manual_diagnostics" in str(result.artifact_paths["artifact_dir"])
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()


def test_ready_non_diagnostic_fixture_writes_preview_artifacts_under_outputs_only(tmp_path: Path) -> None:
    readiness = _write_readiness_artifact(
        tmp_path / "outputs" / "reports" / "readiness" / "ready_case",
        [_ready_readiness_row("000001")],
        review_rows=[_complete_review_row("000001")],
    )

    result = build_pit_universe_export_staging(export_readiness=readiness, output_dir=tmp_path / "outputs" / "reports" / "staging")

    assert result.staging_status == "EXPORT_STAGING_DRY_RUN_CREATED"
    assert result.export_ready_input_count == 1
    assert result.staged_row_count == 1
    assert result.blocked_count == 0
    assert result.staged_universe_frame["symbol"].tolist() == ["000001"]
    assert result.artifact_paths["combined_preview_csv"].exists()
    assert result.per_signal_date_paths["2024-04-02"].exists()
    assert str(result.artifact_paths["artifact_dir"]).replace("\\", "/").find("/outputs/reports/") >= 0
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()


def test_duplicate_ready_keys_block_staging(tmp_path: Path) -> None:
    readiness = _write_readiness_artifact(
        tmp_path,
        [_ready_readiness_row("000001"), _ready_readiness_row("000001")],
        review_rows=[_complete_review_row("000001")],
    )

    result = build_pit_universe_export_staging(export_readiness=readiness, output_dir=tmp_path / "out")

    assert result.duplicate_key_count == 2
    assert result.staged_row_count == 0
    assert set(result.staging_frame["staging_status"]) == {"EXPORT_STAGING_BLOCKED_DUPLICATES"}


def test_missing_required_universe_columns_block_staging(tmp_path: Path) -> None:
    review_row = _complete_review_row("000001")
    review_row["name"] = ""
    readiness = _write_readiness_artifact(
        tmp_path,
        [_ready_readiness_row("000001")],
        review_rows=[review_row],
    )

    result = build_pit_universe_export_staging(export_readiness=readiness, output_dir=tmp_path / "out")

    assert result.staging_status == "EXPORT_STAGING_BLOCKED_MISSING_COLUMNS"
    assert result.staged_row_count == 0
    assert result.missing_required_columns_count == 1
    assert "name" in result.staging_frame.iloc[0]["staging_blocker_reason"]


def test_cli_pit_universe_export_staging_works(tmp_path: Path, capsys) -> None:
    readiness = _write_readiness_artifact(tmp_path, [_blocked_readiness_row("000001")])

    code = cli.main(
        [
            "pit-universe-export-staging",
            "--export-readiness",
            str(readiness),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    output = capsys.readouterr()
    assert code == 0
    assert "staging_id:" in output.out
    assert "staging_status: EXPORT_STAGING_BLOCKED_NO_READY_ROWS" in output.out
    assert "No data/raw write, data/processed write" in output.out


def _write_readiness_artifact(
    root: Path,
    readiness_rows: list[dict],
    *,
    review_rows: list[dict] | None = None,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    readiness = root / "pit_universe_overlay_export_readiness.csv"
    review = root / "reviewed_pit_universe_overlay.csv"
    pd.DataFrame(readiness_rows).to_csv(readiness, index=False)
    pd.DataFrame(review_rows or [_complete_review_row(row["symbol"]) for row in readiness_rows]).to_csv(review, index=False)
    metadata = {
        "export_readiness_id": "readiness001",
        "status": "PASS",
        "readiness_status": "EXPORT_READY_FOR_DRY_RUN",
        "review": str(review),
        "would_write_data_raw": False,
        "would_write_data_processed": False,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
    }
    (root / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return readiness


def _blocked_readiness_row(symbol: str) -> dict:
    row = _ready_readiness_row(symbol)
    row.update(
        {
            "review_status": "NEEDS_MANUAL_REVIEW",
            "include_flag": False,
            "valid_for_signal_date": False,
            "export_ready": False,
            "export_readiness_status": "EXPORT_BLOCKED_NEEDS_MORE_EVIDENCE",
            "export_blocker_reason": "review_status must be APPROVED_FOR_PIT_UNIVERSE before export readiness",
        }
    )
    return row


def _ready_readiness_row(symbol: str) -> dict:
    return {
        "export_readiness_id": "readiness001",
        "review_id": "review001",
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "review_status": "APPROVED_FOR_PIT_UNIVERSE",
        "include_flag": True,
        "valid_for_signal_date": True,
        "export_ready": True,
        "export_readiness_status": "EXPORT_READY_FOR_DRY_RUN",
        "export_blocker_reason": "",
        "required_column_missing_count": 0,
        "missing_required_columns": "",
        "reviewer": "reviewer-a",
        "reviewed_at": "2024-05-29T10:00:00+08:00",
        "evidence_source": "LOCAL_REVIEW",
        "evidence_path": "outputs/reports/manual_diagnostics/evidence.csv",
        "evidence_reference": "",
        "survivorship_bias_warning": True,
        "survivorship_bias_resolved": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "export_readiness_only": True,
    }


def _complete_review_row(symbol: str) -> dict:
    return {
        "review_id": "review001",
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "as_of_date": "2024-04-02",
        "name": f"Name {symbol}",
        "instrument_type": "STOCK",
        "exchange": "SZSE",
        "listed_date": "1991-04-03",
        "delisted_date": "",
        "is_active": True,
        "is_st": False,
        "is_suspended": False,
        "industry": "UNKNOWN",
        "min_lot": 100,
        "t_plus_rule": "T+1",
        "available_time": "2024-04-02 08:00:00",
        "revision_id": "review001",
        "source": "LOCAL_REVIEWED_PIT_OVERLAY",
        "reviewer": "reviewer-a",
        "reviewed_at": "2024-05-29T10:00:00+08:00",
        "evidence_source": "LOCAL_REVIEW",
        "evidence_path": "outputs/reports/manual_diagnostics/evidence.csv",
        "evidence_reference": "",
    }
