import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import PaperArtifactHealthSettings
from quant_replay_system.paper_artifact_health import (
    build_artifact_health_frame,
    check_paper_artifact_health,
    summarize_artifact_health,
)
from quant_replay_system.paper_artifact_index import build_paper_artifact_index


def test_health_check_passes_for_valid_artifact_index(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)

    result = check_paper_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0


def test_missing_report_file_produces_error(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "paper_report.md").unlink()

    result = check_paper_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert _has_issue(result.health_frame, "FILE_NOT_FOUND", "report_path")


def test_missing_metadata_file_produces_error(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "metadata.json").unlink()

    result = check_paper_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert _has_issue(result.health_frame, "FILE_NOT_FOUND", "metadata_path")


def test_unreadable_csv_produces_error(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "decisions.csv").write_bytes(b"\xff\xfe\x00\x00")

    result = check_paper_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert _has_issue(result.health_frame, "CSV_UNREADABLE", "decisions_path")


def test_unreadable_json_produces_error(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "metadata.json").write_text("{", encoding="utf-8")

    result = check_paper_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert _has_issue(result.health_frame, "JSON_UNREADABLE", "metadata_path")


def test_empty_required_csv_produces_configured_warning(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "decisions.csv").write_text("decision_id,symbol\n", encoding="utf-8")

    result = check_paper_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "WARN"
    issue = _issue_row(result.health_frame, "CSV_EMPTY", "decisions_path")
    assert issue["severity"] == "WARN"


def test_missing_no_live_trading_statement_uses_configured_severity(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "paper_report.md").write_text("Daily paper report without safety text.", encoding="utf-8")

    warn_result = check_paper_artifact_health(index_path=index_path, output_dir=tmp_path / "health_warn")
    fail_result = check_paper_artifact_health(
        index_path=index_path,
        output_dir=tmp_path / "health_fail",
        settings=PaperArtifactHealthSettings(missing_no_live_statement_severity="ERROR"),
    )

    assert warn_result.status == "WARN"
    assert _issue_row(warn_result.health_frame, "MISSING_NO_LIVE_TRADING_STATEMENT", "report_path")["severity"] == "WARN"
    assert fail_result.status == "FAIL"
    assert _issue_row(fail_result.health_frame, "MISSING_NO_LIVE_TRADING_STATEMENT", "report_path")["severity"] == "ERROR"


def test_missing_required_metadata_field_produces_configured_warning(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)
    metadata_path = _artifact_file(tmp_path, "metadata.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.pop("paper_trading_only")
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    result = check_paper_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.status == "WARN"
    assert _has_issue(result.health_frame, "MISSING_REQUIRED_METADATA_FIELD", "metadata_path")


def test_health_artifacts_are_written(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)

    result = check_paper_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.artifact_paths["artifact_health_report"].exists()
    assert result.artifact_paths["artifact_health_issues"].exists()
    assert result.artifact_paths["artifact_health_summary"].exists()
    assert result.artifact_paths["metadata"].exists()


def test_health_csvs_are_readable_by_pandas(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)

    result = check_paper_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    pd.read_csv(result.artifact_paths["artifact_health_issues"])
    summary = pd.read_csv(result.artifact_paths["artifact_health_summary"])
    assert summary.iloc[0]["status"] == "PASS"


def test_health_metadata_json_is_written(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)

    result = check_paper_artifact_health(index_path=index_path, output_dir=tmp_path / "health")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["status"] == "PASS"
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_cli_paper_health_check_works(tmp_path: Path, capsys) -> None:
    index_path = _build_valid_index(tmp_path)

    code = cli.main(["paper-health-check", "--index", str(index_path), "--output-dir", str(tmp_path / "health")])
    output = capsys.readouterr()

    assert code == 0
    assert "Health status: PASS" in output.out
    assert "Report path:" in output.out


def test_cli_paper_health_check_exits_nonzero_on_fail_by_default(tmp_path: Path, capsys) -> None:
    index_path = _build_valid_index(tmp_path)
    _artifact_file(tmp_path, "paper_report.md").unlink()

    code = cli.main(["paper-health-check", "--index", str(index_path), "--output-dir", str(tmp_path / "health")])
    output = capsys.readouterr()

    assert code == 1
    assert "Health status: FAIL" in output.out


def test_cli_paper_health_check_prints_no_live_statement(tmp_path: Path, capsys) -> None:
    index_path = _build_valid_index(tmp_path)

    code = cli.main(["paper-health-check", "--index", str(index_path), "--output-dir", str(tmp_path / "health")])
    output = capsys.readouterr()

    assert code == 0
    assert "No live trading or broker API was invoked." in output.out


def test_health_check_output_is_deterministic(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)

    first = check_paper_artifact_health(index_path=index_path, output_dir=tmp_path / "health")
    second = check_paper_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert first.health_check_id == second.health_check_id
    assert first.health_frame.to_dict("records") == second.health_frame.to_dict("records")
    assert first.summary_frame.to_dict("records") == second.summary_frame.to_dict("records")


def test_health_check_does_not_invoke_live_trading_or_broker(tmp_path: Path) -> None:
    index_path = _build_valid_index(tmp_path)

    result = check_paper_artifact_health(index_path=index_path, output_dir=tmp_path / "health")

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["paper_trading_only"] is True


def test_health_frame_detects_unsupported_artifact_type() -> None:
    index_df = pd.DataFrame([{"artifact_type": "UNKNOWN", "artifact_id": "x"}])

    frame = build_artifact_health_frame(index_df)
    summary = summarize_artifact_health(frame, checked_artifact_count=1)

    assert _has_issue(frame, "UNSUPPORTED_ARTIFACT_TYPE", "artifact_type")
    assert summary.iloc[0]["status"] == "FAIL"


def _build_valid_index(tmp_path: Path) -> Path:
    root = tmp_path / "paper_trading"
    _daily_artifact(root)
    index = build_paper_artifact_index(root=root, output_dir=tmp_path / "index")
    return index.artifact_paths["paper_artifact_index_csv"]


def _daily_artifact(root: Path) -> Path:
    folder = root / "daily" / "2024-05-20_daily-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "paper_report.md"
    decisions = folder / "decisions.csv"
    fills = folder / "fills.csv"
    daily_summary = folder / "daily_summary.csv"
    reconciliation_report = folder / "reconciliation_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    reconciliation_report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    pd.DataFrame([{"decision_id": "d1", "symbol": "AAA"}]).to_csv(decisions, index=False)
    pd.DataFrame([{"fill_id": "f1", "symbol": "AAA"}]).to_csv(fills, index=False)
    pd.DataFrame([{"paper_cash": 9000.0, "total_equity": 10050.0}]).to_csv(daily_summary, index=False)
    metadata = {
        "paper_date": "2024-05-20T00:00:00",
        "journal_id": "daily-a",
        "created_at": "2024-05-20T00:00:00",
        "decision_count": 1,
        "fill_count": 1,
        "open_position_count": 1,
        "closed_trade_count": 0,
        "reconciliation": {
            "status": "PASS",
            "report_path": str(reconciliation_report),
            "issue_count": 0,
            "error_count": 0,
            "warning_count": 0,
        },
        "output_files": {
            "paper_report": str(report),
            "decisions": str(decisions),
            "fills": str(fills),
            "daily_summary": str(daily_summary),
        },
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }
    (folder / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return folder


def _artifact_file(tmp_path: Path, filename: str) -> Path:
    return tmp_path / "paper_trading" / "daily" / "2024-05-20_daily-a" / filename


def _has_issue(frame: pd.DataFrame, issue_code: str, path_field: str) -> bool:
    if frame.empty:
        return False
    mask = (frame["issue_code"] == issue_code) & (frame["path_field"] == path_field)
    return bool(mask.any())


def _issue_row(frame: pd.DataFrame, issue_code: str, path_field: str) -> dict:
    rows = frame.loc[(frame["issue_code"] == issue_code) & (frame["path_field"] == path_field)]
    assert not rows.empty
    return rows.iloc[0].to_dict()
