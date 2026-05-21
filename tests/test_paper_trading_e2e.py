import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli


PAPER_DATE = "2024-03-05"


def test_manual_paper_trading_e2e_cli_workflow(tmp_path: Path, capsys) -> None:
    candidates_path = tmp_path / "candidates.csv"
    _candidate_rows().to_csv(candidates_path, index=False)

    initial_daily_dir = tmp_path / "daily_initial"
    initial_code = cli.main(
        [
            "paper-daily",
            "--date",
            PAPER_DATE,
            "--candidates",
            str(candidates_path),
            "--output-dir",
            str(initial_daily_dir),
            "--journal-id",
            "initial",
        ]
    )
    initial_output = capsys.readouterr()
    initial_artifact_dir = initial_daily_dir / f"{PAPER_DATE}_initial"
    initial_decisions_path = initial_artifact_dir / "decisions.csv"
    initial_report_path = initial_artifact_dir / "paper_report.md"

    assert initial_code == 0
    assert initial_decisions_path.exists()
    assert initial_report_path.exists()
    assert "No live trading or broker API was invoked." in initial_output.out
    assert "No broker or live trading integration was invoked" in initial_report_path.read_text(encoding="utf-8")

    initial_decisions = pd.read_csv(initial_decisions_path)
    review_updates_path = tmp_path / "review_updates.csv"
    _review_updates(initial_decisions).to_csv(review_updates_path, index=False)

    review_dir = tmp_path / "reviews"
    review_code = cli.main(
        [
            "paper-review-decisions",
            "--decisions",
            str(initial_decisions_path),
            "--updates",
            str(review_updates_path),
            "--reviewer-id",
            "e2e-reviewer",
            "--output-dir",
            str(review_dir),
        ]
    )
    review_output = capsys.readouterr()
    reviewed_decisions_path = _single_artifact_file(review_dir, "reviewed_decisions.csv")
    review_report_path = reviewed_decisions_path.parent / "paper_review_report.md"

    assert review_code == 0
    assert reviewed_decisions_path.exists()
    assert review_report_path.exists()
    assert "No live trading or broker API was invoked." in review_output.out
    assert "No broker or live trading integration was invoked" in review_report_path.read_text(encoding="utf-8")

    reviewed = pd.read_csv(reviewed_decisions_path)
    statuses = dict(zip(reviewed["symbol"], reviewed["manual_review_status"]))
    assert statuses == {
        "AAA": "APPROVED_FOR_PAPER",
        "BBB": "REJECTED",
        "CCC": "WATCH_ONLY",
    }

    approved_fill_path = tmp_path / "fills_approved.csv"
    _fills_for_symbol(reviewed, "AAA").to_csv(approved_fill_path, index=False)

    reviewed_daily_dir = tmp_path / "daily_reviewed_no_fills"
    reviewed_daily_code = cli.main(
        [
            "paper-daily",
            "--date",
            PAPER_DATE,
            "--candidates",
            str(candidates_path),
            "--reviewed-decisions",
            str(reviewed_decisions_path),
            "--output-dir",
            str(reviewed_daily_dir),
            "--journal-id",
            "reviewed",
        ]
    )
    reviewed_daily_output = capsys.readouterr()
    reviewed_daily_decisions = pd.read_csv(reviewed_daily_dir / f"{PAPER_DATE}_reviewed" / "decisions.csv")
    reviewed_daily_statuses = dict(zip(reviewed_daily_decisions["symbol"], reviewed_daily_decisions["manual_review_status"]))

    assert reviewed_daily_code == 0
    assert reviewed_daily_statuses == statuses
    assert "candidates input ignored" in reviewed_daily_output.out
    assert "reviewed_decisions_used: True" in reviewed_daily_output.out

    approved_reconcile_dir = tmp_path / "reconcile_approved"
    approved_reconcile_code = cli.main(
        [
            "paper-reconcile-fills",
            "--decisions",
            str(reviewed_decisions_path),
            "--fills",
            str(approved_fill_path),
            "--output-dir",
            str(approved_reconcile_dir),
        ]
    )
    approved_reconcile_output = capsys.readouterr()
    approved_reconcile_report = _single_artifact_file(approved_reconcile_dir, "reconciliation_report.md")

    assert approved_reconcile_code == 0
    assert "Reconciliation status: PASS" in approved_reconcile_output.out
    assert approved_reconcile_report.exists()
    assert "No broker or live trading integration was invoked" in approved_reconcile_report.read_text(encoding="utf-8")

    for symbol in ["BBB", "CCC"]:
        rejected_or_watch_path = tmp_path / f"fills_{symbol}.csv"
        _fills_for_symbol(reviewed, symbol).to_csv(rejected_or_watch_path, index=False)
        fail_dir = tmp_path / f"reconcile_{symbol}"
        fail_code = cli.main(
            [
                "paper-reconcile-fills",
                "--decisions",
                str(reviewed_decisions_path),
                "--fills",
                str(rejected_or_watch_path),
                "--output-dir",
                str(fail_dir),
                "--allow-fail",
            ]
        )
        fail_output = capsys.readouterr()
        fail_report = _single_artifact_file(fail_dir, "reconciliation_report.md")

        assert fail_code == 0
        assert "Reconciliation status: FAIL" in fail_output.out
        assert fail_report.exists()
        assert "DECISION_NOT_APPROVED" in fail_report.read_text(encoding="utf-8")

    final_daily_dir = tmp_path / "daily_final"
    final_code = cli.main(
        [
            "paper-daily",
            "--date",
            PAPER_DATE,
            "--reviewed-decisions",
            str(reviewed_decisions_path),
            "--fills",
            str(approved_fill_path),
            "--output-dir",
            str(final_daily_dir),
            "--journal-id",
            "final",
        ]
    )
    final_output = capsys.readouterr()
    final_artifact_dir = final_daily_dir / f"{PAPER_DATE}_final"
    final_report_path = final_artifact_dir / "paper_report.md"
    final_metadata_path = final_artifact_dir / "metadata.json"

    assert final_code == 0
    assert final_report_path.exists()
    assert final_metadata_path.exists()
    assert "No live trading or broker API was invoked." in final_output.out
    assert "No broker or live trading integration was invoked" in final_report_path.read_text(encoding="utf-8")

    metadata = json.loads(final_metadata_path.read_text(encoding="utf-8"))
    assert metadata["reviewed_decisions_used"] is True
    assert metadata["reviewed_decisions_path"] == str(reviewed_decisions_path)
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False
    assert metadata["paper_trading_only"] is True


def _candidate_rows() -> pd.DataFrame:
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
                "source_run_id": "e2e-run",
                "source_report_path": "outputs/reports/e2e-run/report.md",
            },
            {
                "decision_date": pd.Timestamp(PAPER_DATE),
                "symbol": "BBB",
                "name": "BBB Fund",
                "action": "PAPER_TRADE",
                "final_score": 72.0,
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "eligible",
                "rank": 2,
                "source_run_id": "e2e-run",
                "source_report_path": "outputs/reports/e2e-run/report.md",
            },
            {
                "decision_date": pd.Timestamp(PAPER_DATE),
                "symbol": "CCC",
                "name": "CCC Fund",
                "action": "OBSERVE",
                "final_score": 66.0,
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "watch",
                "rank": 3,
                "source_run_id": "e2e-run",
                "source_report_path": "outputs/reports/e2e-run/report.md",
            },
        ]
    )


def _review_updates(decisions: pd.DataFrame) -> pd.DataFrame:
    status_by_symbol = {
        "AAA": ("APPROVED_FOR_PAPER", "SCORE_CONFIRMED", "approved for paper fill"),
        "BBB": ("REJECTED", "RISK_TOO_HIGH", "risk rejected"),
        "CCC": ("WATCH_ONLY", "WATCHLIST_ONLY", "watchlist only"),
    }
    rows = []
    for row in decisions.to_dict("records"):
        status, reason, note = status_by_symbol[str(row["symbol"])]
        rows.append(
            {
                "decision_id": row["decision_id"],
                "manual_review_status": status,
                "manual_review_notes": note,
                "reviewer_id": "",
                "review_reason_code": reason,
            }
        )
    return pd.DataFrame(rows)


def _fills_for_symbol(reviewed: pd.DataFrame, symbol: str) -> pd.DataFrame:
    decision = reviewed.loc[reviewed["symbol"] == symbol].iloc[0]
    fill_price = 10.0 if symbol == "AAA" else 20.0 if symbol == "BBB" else 30.0
    quantity = 100
    gross = fill_price * quantity
    return pd.DataFrame(
        [
            {
                "fill_id": f"fill-{symbol.lower()}",
                "decision_id": decision["decision_id"],
                "symbol": symbol,
                "side": "BUY",
                "fill_date": pd.Timestamp(PAPER_DATE),
                "fill_price": fill_price,
                "quantity": quantity,
                "gross_notional": gross,
                "fees": 0.0,
                "slippage": 0.0,
                "net_cash_flow": -gross,
                "fill_source": "MANUAL",
                "manual_notes": "manual smoke-test fill",
            }
        ]
    )


def _single_artifact_file(root: Path, filename: str) -> Path:
    matches = sorted(root.glob(f"*/{filename}"))
    assert len(matches) == 1
    return matches[0]
