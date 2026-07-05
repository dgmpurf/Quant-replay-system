import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli


def test_cli_no_context_smoke_writes_all_expected_files(tmp_path: Path, capsys) -> None:
    code = cli.main(
        [
            "personal-mvp-daily-advisory-review",
            "--root",
            str(tmp_path / "reports"),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "daily_review_run_id:" in output.out
    assert "status: DAILY_ADVISORY_REVIEW_NO_LOCAL_CONTEXT" in output.out
    assert "row_count: 0" in output.out
    assert "report_path:" in output.out
    assert "No broker API was invoked." in output.out
    assert "No orders were placed." in output.out
    assert "No messages were sent." in output.out
    assert "No trading was authorized." in output.out

    artifact_dir = _artifact_dir_from_output(output.out)
    assert (artifact_dir / "metadata.json").exists()
    assert (artifact_dir / "daily_advisory_review_report.md").exists()
    assert (artifact_dir / "daily_advisory_review_rows.csv").exists()
    assert (artifact_dir / "daily_advisory_review_summary.csv").exists()
    assert (artifact_dir / "single_symbol_drilldown_index.csv").exists()
    assert (artifact_dir / "manual_review_checklist.csv").exists()
    assert (artifact_dir / "safety_flags.json").exists()


def test_cli_fixture_smoke_writes_rows_and_summary(tmp_path: Path, capsys) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root)

    code = cli.main(
        [
            "personal-mvp-daily-advisory-review",
            "--root",
            str(root),
            "--review-date",
            "2024-05-20",
            "--output-dir",
            str(tmp_path / "out"),
            "--max-symbols",
            "10",
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "status: DAILY_ADVISORY_REVIEW_READY_FOR_MANUAL_REVIEW" in output.out
    assert "row_count: 2" in output.out
    artifact_dir = _artifact_dir_from_output(output.out)
    rows = pd.read_csv(artifact_dir / "daily_advisory_review_rows.csv", dtype={"symbol": str}).fillna("")
    summary = pd.read_csv(artifact_dir / "daily_advisory_review_summary.csv", dtype=str).fillna("").iloc[0]

    assert rows["symbol"].tolist() == ["000001", "600519"]
    assert summary["row_count"] == "2"
    assert summary["watch_count"] == "1"
    assert summary["review_buy_candidate_count"] == "1"


def test_cli_output_keeps_safety_flags_false(tmp_path: Path, capsys) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root)

    code = cli.main(
        [
            "personal-mvp-daily-advisory-review",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "out"),
            "--no-include-paper-context",
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    artifact_dir = _artifact_dir_from_output(output.out)
    safety = json.loads((artifact_dir / "safety_flags.json").read_text(encoding="utf-8"))
    metadata = json.loads((artifact_dir / "metadata.json").read_text(encoding="utf-8"))

    assert safety["buy_review_allowed"] is False
    assert safety["trading_allowed"] is False
    assert safety["broker_api_called"] is False
    assert safety["order_placed"] is False
    assert safety["message_sent"] is False
    assert metadata["include_paper_context"] is False


def _artifact_dir_from_output(output: str) -> Path:
    for line in output.splitlines():
        if line.startswith("artifact_dir:"):
            return Path(line.split(":", 1)[1].strip())
    raise AssertionError(output)


def _write_signal_artifact(root: Path) -> None:
    artifact = root / "signals" / "signal-run-cli"
    artifact.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "signal_id": "signal-000001",
                "signal_run_id": "signal-run-cli",
                "signal_date": "2024-05-20",
                "decision_date": "2024-05-20",
                "symbol": "000001",
                "name": "Name 000001",
                "instrument_type": "stock",
                "universe_name": "stock_core",
                "advisory_action": "WATCH",
                "final_score": 60.0,
                "confidence_level": "medium",
                "reason_summary": "watch reason",
                "risk_notes": "risk note",
                "data_source_notes": "data note",
                "demo_mode": False,
                "not_strategy_recommendation": False,
                "requires_manual_confirmation": True,
                "auto_order_allowed": False,
                "no_live_trading": True,
                "no_broker_api": True,
                "no_message_sent": True,
            },
            {
                "signal_id": "signal-600519",
                "signal_run_id": "signal-run-cli",
                "signal_date": "2024-05-20",
                "decision_date": "2024-05-20",
                "symbol": "600519",
                "name": "Name 600519",
                "instrument_type": "stock",
                "universe_name": "stock_core",
                "advisory_action": "REVIEW_BUY_CANDIDATE",
                "final_score": 80.0,
                "confidence_level": "medium",
                "reason_summary": "manual review reason",
                "risk_notes": "risk note",
                "data_source_notes": "data note",
                "demo_mode": False,
                "not_strategy_recommendation": False,
                "requires_manual_confirmation": True,
                "auto_order_allowed": False,
                "no_live_trading": True,
                "no_broker_api": True,
                "no_message_sent": True,
            },
        ]
    ).to_csv(artifact / "signals.csv", index=False)
    (artifact / "signal_advisory_report.md").write_text("# Signal report\n", encoding="utf-8")
    (artifact / "metadata.json").write_text(
        json.dumps(
            {
                "signal_run_id": "signal-run-cli",
                "status": "SIGNAL_ADVISORY_READY_FOR_REVIEW",
                "workflow_stage": "SIGNAL_ADVISORY_READY_FOR_REVIEW",
                "signal_count": 2,
                "report_path": str(artifact / "signal_advisory_report.md"),
                "signals_path": str(artifact / "signals.csv"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
