import json
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

from quant_replay_system.config import load_settings
from quant_replay_system.daily_paper_runner import (
    DailyPaperRunResult,
    load_candidates_for_paper_trading,
    load_existing_paper_fills,
    run_daily_paper_trading,
)
from quant_replay_system.paper_trading import create_paper_decision_log, record_paper_fill


PAPER_DATE = "2024-03-05"


def test_runner_creates_decision_log_from_candidates_dataframe(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert isinstance(result, DailyPaperRunResult)
    assert result.decision_count == 2
    assert set(result.decisions["symbol"]) == {"AAA", "BBB"}


def test_runner_loads_candidates_from_csv(tmp_path: Path) -> None:
    candidate_path = tmp_path / "candidates.csv"
    _candidates().to_csv(candidate_path, index=False)

    result = _run(tmp_path, candidates=None, candidates_path=candidate_path)

    assert result.decision_count == 2
    assert result.decisions.iloc[0]["symbol"] == "AAA"


def test_runner_handles_missing_optional_candidate_columns(tmp_path: Path) -> None:
    result = _run(tmp_path, candidates=pd.DataFrame([{"symbol": "AAA"}]), fills_path=tmp_path / "missing.csv")

    assert result.decision_count == 1
    assert result.decisions.iloc[0]["manual_review_status"] == "PENDING_REVIEW"
    assert result.decisions.iloc[0]["risk_precheck_status"] == ""


def test_runner_continues_with_empty_fills_if_fills_path_is_missing(tmp_path: Path) -> None:
    result = _run(tmp_path, fills_path=tmp_path / "missing_fills.csv")

    assert result.fill_count == 0
    assert any("Fills file not found" in warning for warning in result.warnings)


def test_runner_loads_existing_fills_when_provided(tmp_path: Path) -> None:
    fills_path = _fills_path(tmp_path, round_trip=False)
    result = _run(tmp_path, fills_path=fills_path)

    assert result.fill_count == 1
    assert result.fills.iloc[0]["side"] == "BUY"


def test_runner_builds_open_positions(tmp_path: Path) -> None:
    fills_path = _fills_path(tmp_path, round_trip=False)
    result = _run(tmp_path, fills_path=fills_path)

    assert result.open_position_count == 1
    assert result.open_positions.iloc[0]["symbol"] == "AAA"


def test_runner_builds_closed_trades(tmp_path: Path) -> None:
    fills_path = _fills_path(tmp_path, round_trip=True)
    result = _run(tmp_path, fills_path=fills_path)

    assert result.closed_trade_count == 1
    assert result.closed_trades.iloc[0]["realized_pnl"] == 200.0


def test_runner_generates_daily_summary(tmp_path: Path) -> None:
    fills_path = _fills_path(tmp_path, round_trip=True)
    result = _run(tmp_path, fills_path=fills_path)

    assert len(result.daily_summary) == 1
    assert result.daily_summary.iloc[0]["paper_date"] == pd.Timestamp(PAPER_DATE)
    assert result.daily_summary.iloc[0]["total_realized_pnl"] == 200.0


def test_runner_writes_all_expected_artifacts(tmp_path: Path) -> None:
    result = _run(tmp_path, fills_path=_fills_path(tmp_path, round_trip=True))

    for key in ["paper_report", "decisions", "fills", "open_positions", "closed_trades", "daily_summary", "metadata"]:
        assert result.artifact_paths[key].exists()


def test_runner_csv_artifacts_are_readable_by_pandas(tmp_path: Path) -> None:
    result = _run(tmp_path, fills_path=_fills_path(tmp_path, round_trip=True))

    for key in ["decisions", "fills", "open_positions", "closed_trades", "daily_summary"]:
        exported = pd.read_csv(result.artifact_paths[key])
        assert isinstance(exported, pd.DataFrame)


def test_runner_metadata_json_is_written(tmp_path: Path) -> None:
    result = _run(tmp_path)
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["journal_id"] == result.journal_id
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_runner_report_contains_no_live_trading_statement(tmp_path: Path) -> None:
    result = _run(tmp_path)
    content = result.artifact_paths["paper_report"].read_text(encoding="utf-8")

    assert "No broker or live trading integration was invoked" in content


def test_deterministic_journal_id_and_output_path_for_same_inputs(tmp_path: Path) -> None:
    first = _run(tmp_path)
    second = _run(tmp_path)

    assert first.journal_id == second.journal_id
    assert first.artifact_paths["artifact_dir"] == second.artifact_paths["artifact_dir"]


def test_runner_output_is_deterministic_for_same_inputs(tmp_path: Path) -> None:
    first = _run(tmp_path, fills_path=_fills_path(tmp_path, round_trip=True))
    second = _run(tmp_path, fills_path=_fills_path(tmp_path, round_trip=True))

    assert_frame_equal(first.decisions, second.decisions)
    assert_frame_equal(first.fills, second.fills)
    assert_frame_equal(first.open_positions, second.open_positions)
    assert_frame_equal(first.closed_trades, second.closed_trades)
    assert_frame_equal(first.daily_summary, second.daily_summary)


def test_runner_no_broker_or_live_trading_integration_is_invoked(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["paper_trading_only"] is True


def test_load_candidates_for_paper_trading_rejects_missing_input() -> None:
    try:
        load_candidates_for_paper_trading()
    except ValueError as exc:
        assert "required" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_load_existing_paper_fills_missing_path_returns_warning(tmp_path: Path) -> None:
    fills, warnings = load_existing_paper_fills(tmp_path / "missing.csv")

    assert fills.empty
    assert warnings


def _run(
    tmp_path: Path,
    *,
    candidates: pd.DataFrame | None = None,
    candidates_path: Path | None = None,
    fills_path: Path | None = None,
) -> DailyPaperRunResult:
    return run_daily_paper_trading(
        PAPER_DATE,
        candidates=_candidates() if candidates is None and candidates_path is None else candidates,
        candidates_path=candidates_path,
        fills_path=fills_path,
        mark_prices=_mark_prices(),
        output_dir=tmp_path / "paper_daily",
        config=_settings(tmp_path),
    )


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "daily_paper_runner": settings.daily_paper_runner.model_copy(
                update={"output_dir": tmp_path / "paper_daily", "write_artifacts": True}
            ),
            "paper_trading": settings.paper_trading.model_copy(
                update={"output_dir": tmp_path / "paper_trading", "write_artifacts": False}
            ),
            "paper_reconciliation": settings.paper_reconciliation.model_copy(
                update={"output_dir": tmp_path / "reconciliation", "write_artifacts": True}
            ),
        }
    )


def _fills_path(tmp_path: Path, *, round_trip: bool) -> Path:
    decisions = create_paper_decision_log(
        _candidates(),
        decision_date=PAPER_DATE,
        source_run_id="run123",
        source_report_path="outputs/reports/run123/report.md",
        manual_review_status="APPROVED_FOR_PAPER",
    )
    fills = record_paper_fill(
        decisions,
        decision_id=decisions.iloc[0]["decision_id"],
        side="BUY",
        fill_date="2024-03-04",
        fill_price=10.0,
        quantity=100,
        settings=_settings(tmp_path).paper_trading,
    )
    if round_trip:
        fills = record_paper_fill(
            decisions,
            fills,
            decision_id=decisions.iloc[0]["decision_id"],
            side="SELL",
            fill_date="2024-03-05",
            fill_price=12.0,
            quantity=100,
            settings=_settings(tmp_path).paper_trading,
        )
    path = tmp_path / ("fills_round_trip.csv" if round_trip else "fills_open.csv")
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
                "technical_score": 75.0,
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "eligible",
                "rank": 1,
                "source_run_id": "run123",
                "source_report_path": "outputs/reports/run123/report.md",
                "manual_review_status": "APPROVED_FOR_PAPER",
            },
            {
                "decision_date": pd.Timestamp(PAPER_DATE),
                "symbol": "BBB",
                "name": "BBB Fund",
                "action": "OBSERVE",
                "final_score": 66.0,
                "technical_score": 55.0,
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "watch",
                "rank": 2,
                "source_run_id": "run123",
                "source_report_path": "outputs/reports/run123/report.md",
                "manual_review_status": "APPROVED_FOR_PAPER",
            },
        ]
    )


def _mark_prices() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"symbol": "AAA", "trade_date": pd.Timestamp("2024-03-04"), "close": 10.0},
            {"symbol": "AAA", "trade_date": pd.Timestamp("2024-03-05"), "close": 12.0},
            {"symbol": "BBB", "trade_date": pd.Timestamp("2024-03-05"), "close": 21.0},
        ]
    )
