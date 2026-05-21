import sys
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.paper_trading import create_paper_decision_log, record_paper_fill


PAPER_DATE = "2024-03-05"


def test_paper_daily_command_runs_with_candidates_csv(tmp_path: Path, capsys) -> None:
    candidates_path = _write_candidates(tmp_path)
    code = cli.main(
        [
            "paper-daily",
            "--date",
            PAPER_DATE,
            "--candidates",
            str(candidates_path),
            "--output-dir",
            str(tmp_path / "daily"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Artifact folder:" in output.out
    assert "decision_count: 2" in output.out


def test_paper_daily_writes_expected_artifacts(tmp_path: Path) -> None:
    candidates_path = _write_candidates(tmp_path)
    code = cli.main(
        [
            "paper-daily",
            "--date",
            PAPER_DATE,
            "--candidates",
            str(candidates_path),
            "--output-dir",
            str(tmp_path / "daily"),
            "--journal-id",
            "cli-test",
        ]
    )
    artifact_dir = tmp_path / "daily" / f"{PAPER_DATE}_cli-test"

    assert code == 0
    for filename in [
        "paper_report.md",
        "decisions.csv",
        "fills.csv",
        "open_positions.csv",
        "closed_trades.csv",
        "daily_summary.csv",
        "metadata.json",
    ]:
        assert (artifact_dir / filename).exists()


def test_paper_daily_prints_no_live_trading_statement(tmp_path: Path, capsys) -> None:
    candidates_path = _write_candidates(tmp_path)
    code = cli.main(
        [
            "paper-daily",
            "--date",
            PAPER_DATE,
            "--candidates",
            str(candidates_path),
            "--output-dir",
            str(tmp_path / "daily"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "No live trading or broker API was invoked." in output.out


def test_paper_daily_handles_missing_fills_path_as_warning_not_failure(tmp_path: Path, capsys) -> None:
    candidates_path = _write_candidates(tmp_path)
    code = cli.main(
        [
            "paper-daily",
            "--date",
            PAPER_DATE,
            "--candidates",
            str(candidates_path),
            "--fills",
            str(tmp_path / "missing_fills.csv"),
            "--output-dir",
            str(tmp_path / "daily"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "WARNING: Fills file not found" in output.out


def test_paper_daily_works_with_reviewed_decisions(tmp_path: Path, capsys) -> None:
    reviewed_path = _write_reviewed_decisions(tmp_path)
    code = cli.main(
        [
            "paper-daily",
            "--date",
            PAPER_DATE,
            "--reviewed-decisions",
            str(reviewed_path),
            "--output-dir",
            str(tmp_path / "daily"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "reviewed_decisions_used: True" in output.out
    assert "decision_count: 2" in output.out


def test_paper_daily_requires_candidates_or_reviewed_decisions(capsys) -> None:
    code = cli.main(["paper-daily", "--date", PAPER_DATE])
    output = capsys.readouterr()

    assert code != 0
    assert "Either --candidates or --reviewed-decisions is required" in output.err


def test_paper_validate_fills_succeeds_on_valid_fills_csv(tmp_path: Path, capsys) -> None:
    fills_path = _write_fills(tmp_path)
    code = cli.main(["paper-validate-fills", "--fills", str(fills_path)])
    output = capsys.readouterr()

    assert code == 0
    assert "Validation passed." in output.out


def test_paper_validate_fills_fails_on_missing_required_columns(tmp_path: Path, capsys) -> None:
    path = tmp_path / "bad_fills.csv"
    pd.DataFrame([{"symbol": "AAA"}]).to_csv(path, index=False)
    code = cli.main(["paper-validate-fills", "--fills", str(path)])
    output = capsys.readouterr()

    assert code != 0
    assert "Missing required columns" in output.err


def test_paper_validate_fills_fails_on_invalid_side(tmp_path: Path, capsys) -> None:
    path = _write_fills(tmp_path, updates={"side": "SHORT"})
    code = cli.main(["paper-validate-fills", "--fills", str(path)])
    output = capsys.readouterr()

    assert code != 0
    assert "Invalid side" in output.err


def test_paper_validate_fills_fails_on_non_positive_quantity(tmp_path: Path, capsys) -> None:
    path = _write_fills(tmp_path, updates={"quantity": 0})
    code = cli.main(["paper-validate-fills", "--fills", str(path)])
    output = capsys.readouterr()

    assert code != 0
    assert "Non-positive quantity" in output.err


def test_paper_validate_fills_fails_on_non_positive_fill_price(tmp_path: Path, capsys) -> None:
    path = _write_fills(tmp_path, updates={"fill_price": -1})
    code = cli.main(["paper-validate-fills", "--fills", str(path)])
    output = capsys.readouterr()

    assert code != 0
    assert "Non-positive fill_price" in output.err


def test_paper_template_fills_writes_template_csv(tmp_path: Path, capsys) -> None:
    output_path = tmp_path / "fills_template.csv"
    code = cli.main(["paper-template-fills", "--output", str(output_path)])
    output = capsys.readouterr()
    exported = pd.read_csv(output_path)

    assert code == 0
    assert "Wrote fills template" in output.out
    assert list(exported.columns) == cli.FILL_COLUMNS


def test_paper_template_fills_does_not_overwrite_existing_file_by_default(tmp_path: Path, capsys) -> None:
    output_path = tmp_path / "fills_template.csv"
    output_path.write_text("keep_me\n", encoding="utf-8")
    code = cli.main(["paper-template-fills", "--output", str(output_path)])
    output = capsys.readouterr()

    assert code != 0
    assert "Refusing to overwrite" in output.err
    assert output_path.read_text(encoding="utf-8") == "keep_me\n"


def test_paper_template_fills_overwrites_when_overwrite_is_passed(tmp_path: Path) -> None:
    output_path = tmp_path / "fills_template.csv"
    output_path.write_text("replace_me\n", encoding="utf-8")
    code = cli.main(["paper-template-fills", "--output", str(output_path), "--overwrite"])

    assert code == 0
    assert list(pd.read_csv(output_path).columns) == cli.FILL_COLUMNS


def test_cli_does_not_import_or_invoke_broker_live_modules(tmp_path: Path, capsys) -> None:
    candidates_path = _write_candidates(tmp_path)
    code = cli.main(
        [
            "paper-daily",
            "--date",
            PAPER_DATE,
            "--candidates",
            str(candidates_path),
            "--output-dir",
            str(tmp_path / "daily"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "No live trading or broker API was invoked." in output.out
    assert not any("broker" in module_name.lower() for module_name in sys.modules)


def _write_candidates(tmp_path: Path) -> Path:
    path = tmp_path / "candidates.csv"
    _candidates().to_csv(path, index=False)
    return path


def _write_reviewed_decisions(tmp_path: Path) -> Path:
    decisions = create_paper_decision_log(
        _candidates(),
        decision_date=PAPER_DATE,
        source_run_id="cli-run",
        source_report_path="outputs/reports/cli-run/report.md",
        manual_review_status="PENDING_REVIEW",
    )
    decisions["manual_review_status"] = ["APPROVED_FOR_PAPER", "WATCH_ONLY"]
    decisions["manual_review_notes"] = ["approved", "watch"]
    decisions["reviewer_id"] = ["cli-reviewer", "cli-reviewer"]
    decisions["review_reason_code"] = ["SCORE_CONFIRMED", "WATCHLIST_ONLY"]
    decisions["review_time"] = [pd.Timestamp(PAPER_DATE), pd.Timestamp(PAPER_DATE)]
    path = tmp_path / "reviewed_decisions.csv"
    decisions.to_csv(path, index=False)
    return path


def _write_fills(tmp_path: Path, updates: dict | None = None) -> Path:
    decisions = create_paper_decision_log(
        _candidates(),
        decision_date=PAPER_DATE,
        source_run_id="cli-run",
        source_report_path="outputs/reports/cli-run/report.md",
        manual_review_status="APPROVED_FOR_PAPER",
    )
    fills = record_paper_fill(
        decisions,
        decision_id=decisions.iloc[0]["decision_id"],
        side="BUY",
        fill_date=PAPER_DATE,
        fill_price=10.0,
        quantity=100,
    )
    if updates:
        for key, value in updates.items():
            fills.loc[0, key] = value
    path = tmp_path / "fills.csv"
    fills.to_csv(path, index=False)
    return path


def _candidates() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "decision_date": pd.Timestamp(PAPER_DATE),
                "symbol": "AAA",
                "name": "AAA Fund",
                "action": "PAPER_TRADE",
                "final_score": 82.5,
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "eligible",
                "rank": 1,
                "source_run_id": "cli-run",
                "source_report_path": "outputs/reports/cli-run/report.md",
            },
            {
                "decision_date": pd.Timestamp(PAPER_DATE),
                "symbol": "BBB",
                "name": "BBB Fund",
                "action": "OBSERVE",
                "final_score": 66.0,
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "watch",
                "rank": 2,
                "source_run_id": "cli-run",
                "source_report_path": "outputs/reports/cli-run/report.md",
            },
        ]
    )
