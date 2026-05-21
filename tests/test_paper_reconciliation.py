import json
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.daily_paper_runner import run_daily_paper_trading
from quant_replay_system.paper_reconciliation import (
    PaperReconciliationResult,
    reconcile_paper_fills,
)
from quant_replay_system.paper_trading import create_paper_decision_log, record_paper_fill


PAPER_DATE = "2024-03-05"


def test_reconciliation_passes_for_valid_decisions_and_fills(tmp_path: Path) -> None:
    decisions = _decisions()
    fills = _valid_buy_fill(decisions)

    result = reconcile_paper_fills(decisions, fills, settings=_settings(tmp_path))

    assert isinstance(result, PaperReconciliationResult)
    assert result.status == "PASS"
    assert result.issue_count == 0


def test_unknown_decision_id_produces_error(tmp_path: Path) -> None:
    decisions = _decisions()
    fills = _valid_buy_fill(decisions)
    fills.loc[0, "decision_id"] = "missing-decision"

    result = reconcile_paper_fills(decisions, fills, settings=_settings(tmp_path))

    assert result.status == "FAIL"
    assert _has_issue(result, "UNKNOWN_DECISION_ID")


def test_symbol_mismatch_produces_error(tmp_path: Path) -> None:
    decisions = _decisions()
    fills = _valid_buy_fill(decisions)
    fills.loc[0, "symbol"] = "BBB"

    result = reconcile_paper_fills(decisions, fills, settings=_settings(tmp_path))

    assert result.status == "FAIL"
    assert _has_issue(result, "SYMBOL_MISMATCH")


def test_pending_review_fill_produces_error(tmp_path: Path) -> None:
    decisions = _decisions(status="PENDING_REVIEW")
    fills = _manual_fill(decisions)

    result = reconcile_paper_fills(decisions, fills, settings=_settings(tmp_path))

    assert result.status == "FAIL"
    assert _has_issue(result, "DECISION_NOT_APPROVED")


def test_rejected_fill_produces_error(tmp_path: Path) -> None:
    decisions = _decisions(status="REJECTED")
    fills = _manual_fill(decisions)

    result = reconcile_paper_fills(decisions, fills, settings=_settings(tmp_path))

    assert result.status == "FAIL"
    assert _has_issue(result, "DECISION_NOT_APPROVED")


def test_invalid_side_produces_error(tmp_path: Path) -> None:
    decisions = _decisions()
    fills = _manual_fill(decisions, side="SHORT")

    result = reconcile_paper_fills(decisions, fills, settings=_settings(tmp_path))

    assert _has_issue(result, "INVALID_SIDE")


def test_non_positive_quantity_produces_error(tmp_path: Path) -> None:
    decisions = _decisions()
    fills = _manual_fill(decisions, quantity=0)

    result = reconcile_paper_fills(decisions, fills, settings=_settings(tmp_path))

    assert _has_issue(result, "NON_POSITIVE_QUANTITY")


def test_non_positive_fill_price_produces_error(tmp_path: Path) -> None:
    decisions = _decisions()
    fills = _manual_fill(decisions, fill_price=0)

    result = reconcile_paper_fills(decisions, fills, settings=_settings(tmp_path))

    assert _has_issue(result, "NON_POSITIVE_FILL_PRICE")


def test_gross_notional_mismatch_produces_error(tmp_path: Path) -> None:
    decisions = _decisions()
    fills = _valid_buy_fill(decisions)
    fills.loc[0, "gross_notional"] = 1.0

    result = reconcile_paper_fills(decisions, fills, settings=_settings(tmp_path))

    assert _has_issue(result, "GROSS_NOTIONAL_MISMATCH")


def test_wrong_buy_net_cash_flow_sign_produces_error(tmp_path: Path) -> None:
    decisions = _decisions()
    fills = _manual_fill(decisions, side="BUY", net_cash_flow=1000.0)

    result = reconcile_paper_fills(decisions, fills, settings=_settings(tmp_path))

    assert _has_issue(result, "BUY_CASH_FLOW_SIGN_ERROR")


def test_wrong_sell_net_cash_flow_sign_produces_error(tmp_path: Path) -> None:
    decisions = _decisions()
    fills = _manual_fill(decisions, side="SELL", net_cash_flow=-1000.0)

    result = reconcile_paper_fills(decisions, fills, settings=_settings(tmp_path))

    assert _has_issue(result, "SELL_CASH_FLOW_SIGN_ERROR")


def test_oversell_produces_error(tmp_path: Path) -> None:
    decisions = _decisions()
    fills = pd.concat(
        [
            _manual_fill(decisions, fill_id="buy-1", side="BUY", quantity=100),
            _manual_fill(decisions, fill_id="sell-1", side="SELL", quantity=200),
        ],
        ignore_index=True,
    )

    result = reconcile_paper_fills(decisions, fills, settings=_settings(tmp_path))

    assert _has_issue(result, "OVERSELL")


def test_duplicate_fill_id_produces_warning(tmp_path: Path) -> None:
    decisions = _decisions()
    fills = pd.concat(
        [
            _manual_fill(decisions, fill_id="duplicate-fill", side="BUY", quantity=100),
            _manual_fill(decisions, fill_id="duplicate-fill", side="BUY", quantity=100),
        ],
        ignore_index=True,
    )

    result = reconcile_paper_fills(decisions, fills, settings=_settings(tmp_path))

    assert result.status == "WARN"
    assert _has_issue(result, "DUPLICATE_FILL_ID", severity="WARN")


def test_negative_cash_produces_error_by_default(tmp_path: Path) -> None:
    decisions = _decisions()
    fills = _manual_fill(decisions, side="BUY", fill_price=10.0, quantity=100)

    result = reconcile_paper_fills(decisions, fills, settings=_settings(tmp_path), initial_cash=500.0)

    assert result.status == "FAIL"
    assert _has_issue(result, "NEGATIVE_CASH")


def test_missing_required_fill_columns_produces_error(tmp_path: Path) -> None:
    decisions = _decisions()
    fills = pd.DataFrame([{"fill_id": "f1", "symbol": "AAA"}])

    result = reconcile_paper_fills(decisions, fills, settings=_settings(tmp_path))

    assert result.status == "FAIL"
    assert _has_issue(result, "MISSING_REQUIRED_COLUMN")


def test_reconciliation_artifacts_are_written_and_readable(tmp_path: Path) -> None:
    decisions = _decisions()
    fills = _valid_buy_fill(decisions)

    result = reconcile_paper_fills(decisions, fills, settings=_settings(tmp_path))

    assert result.artifact_paths["reconciliation_report"].exists()
    assert result.artifact_paths["metadata"].exists()
    issues = pd.read_csv(result.artifact_paths["reconciliation_issues"])
    summary = pd.read_csv(result.artifact_paths["reconciliation_summary"])
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert isinstance(issues, pd.DataFrame)
    assert summary.iloc[0]["status"] == "PASS"
    assert metadata["status"] == "PASS"


def test_daily_paper_runner_records_reconciliation_path_and_status(tmp_path: Path) -> None:
    decisions = _decisions()
    fills_path = tmp_path / "fills.csv"
    _valid_buy_fill(decisions).to_csv(fills_path, index=False)

    result = run_daily_paper_trading(
        PAPER_DATE,
        candidates=_candidates(),
        fills_path=fills_path,
        mark_prices=_mark_prices(),
        output_dir=tmp_path / "daily",
        config=_settings(tmp_path),
    )
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert result.reconciliation_status == "PASS"
    assert result.reconciliation_path is not None
    assert result.reconciliation_path.exists()
    assert metadata["reconciliation"]["status"] == "PASS"


def test_cli_paper_reconcile_fills_works(tmp_path: Path, capsys) -> None:
    decisions_path, fills_path = _write_decisions_and_fills(tmp_path)

    code = cli.main(
        [
            "paper-reconcile-fills",
            "--decisions",
            str(decisions_path),
            "--fills",
            str(fills_path),
            "--output-dir",
            str(tmp_path / "reconciliation"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Reconciliation status: PASS" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_cli_paper_reconcile_fills_exits_nonzero_on_fail_by_default(tmp_path: Path) -> None:
    decisions_path, fills_path = _write_decisions_and_fills(tmp_path)
    fills = pd.read_csv(fills_path)
    fills.loc[0, "decision_id"] = "unknown"
    fills.to_csv(fills_path, index=False)

    code = cli.main(
        [
            "paper-reconcile-fills",
            "--decisions",
            str(decisions_path),
            "--fills",
            str(fills_path),
            "--output-dir",
            str(tmp_path / "reconciliation"),
        ]
    )

    assert code != 0


def test_cli_paper_reconcile_fills_allow_fail_exits_zero_with_fail_report(tmp_path: Path, capsys) -> None:
    decisions_path, fills_path = _write_decisions_and_fills(tmp_path)
    fills = pd.read_csv(fills_path)
    fills.loc[0, "decision_id"] = "unknown"
    fills.to_csv(fills_path, index=False)

    code = cli.main(
        [
            "paper-reconcile-fills",
            "--decisions",
            str(decisions_path),
            "--fills",
            str(fills_path),
            "--output-dir",
            str(tmp_path / "reconciliation"),
            "--allow-fail",
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Reconciliation status: FAIL" in output.out


def test_reconciliation_no_broker_or_live_trading_integration_is_invoked(tmp_path: Path) -> None:
    result = reconcile_paper_fills(_decisions(), _valid_buy_fill(_decisions()), settings=_settings(tmp_path))

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["paper_trading_only"] is True
    assert not any("broker" in module_name.lower() for module_name in sys.modules)


def _has_issue(result: PaperReconciliationResult, issue_code: str, *, severity: str | None = None) -> bool:
    frame = result.reconciliation_frame
    if severity is not None:
        frame = frame.loc[frame["severity"] == severity]
    return issue_code in set(frame["issue_code"])


def _write_decisions_and_fills(tmp_path: Path) -> tuple[Path, Path]:
    decisions = _decisions()
    fills = _valid_buy_fill(decisions)
    decisions_path = tmp_path / "decisions.csv"
    fills_path = tmp_path / "fills.csv"
    decisions.to_csv(decisions_path, index=False)
    fills.to_csv(fills_path, index=False)
    return decisions_path, fills_path


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "daily_paper_runner": settings.daily_paper_runner.model_copy(
                update={"output_dir": tmp_path / "daily", "write_artifacts": True}
            ),
            "paper_trading": settings.paper_trading.model_copy(
                update={"output_dir": tmp_path / "paper_trading", "write_artifacts": False}
            ),
            "paper_reconciliation": settings.paper_reconciliation.model_copy(
                update={"output_dir": tmp_path / "reconciliation", "write_artifacts": True}
            ),
        }
    )


def _decisions(status: str = "APPROVED_FOR_PAPER") -> pd.DataFrame:
    candidates = _candidates()
    candidates["manual_review_status"] = status
    return create_paper_decision_log(
        candidates,
        decision_date=PAPER_DATE,
        source_run_id="reconcile-run",
        source_report_path="outputs/reports/reconcile-run/report.md",
        manual_review_status=status,
    )


def _valid_buy_fill(decisions: pd.DataFrame) -> pd.DataFrame:
    return record_paper_fill(
        decisions,
        decision_id=decisions.iloc[0]["decision_id"],
        side="BUY",
        fill_date=PAPER_DATE,
        fill_price=10.0,
        quantity=100,
        settings=load_settings(Path("config/default.yaml")).paper_trading,
    )


def _manual_fill(
    decisions: pd.DataFrame,
    *,
    fill_id: str = "manual-fill-1",
    decision_index: int = 0,
    side: str = "BUY",
    fill_price: float = 10.0,
    quantity: float = 100.0,
    gross_notional: float | None = None,
    net_cash_flow: float | None = None,
) -> pd.DataFrame:
    decision = decisions.iloc[decision_index]
    side_value = side.upper()
    gross = fill_price * quantity if gross_notional is None else gross_notional
    cash_flow = net_cash_flow
    if cash_flow is None:
        cash_flow = -gross if side_value == "BUY" else gross
    return pd.DataFrame(
        [
            {
                "fill_id": fill_id,
                "decision_id": decision["decision_id"],
                "symbol": decision["symbol"],
                "side": side,
                "fill_date": pd.Timestamp(PAPER_DATE),
                "fill_price": fill_price,
                "quantity": quantity,
                "gross_notional": gross,
                "fees": 0.0,
                "slippage": 0.0,
                "net_cash_flow": cash_flow,
                "fill_source": "MANUAL",
                "manual_notes": "",
            }
        ]
    )


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
                "source_run_id": "reconcile-run",
                "source_report_path": "outputs/reports/reconcile-run/report.md",
                "manual_review_status": "APPROVED_FOR_PAPER",
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
                "source_run_id": "reconcile-run",
                "source_report_path": "outputs/reports/reconcile-run/report.md",
                "manual_review_status": "APPROVED_FOR_PAPER",
            },
        ]
    )


def _mark_prices() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"symbol": "AAA", "trade_date": pd.Timestamp(PAPER_DATE), "close": 12.0},
            {"symbol": "BBB", "trade_date": pd.Timestamp(PAPER_DATE), "close": 21.0},
        ]
    )
