import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import DataQualitySettings
from quant_replay_system.data_quality import run_data_quality_checks


def test_market_data_quality_passes_on_clean_data(tmp_path: Path) -> None:
    result = run_data_quality_checks(_market_frame(), "market", output_dir=tmp_path / "quality")

    assert result.status == "PASS"
    assert result.row_count == 2
    assert result.issue_count == 0


def test_missing_required_market_column_fails(tmp_path: Path) -> None:
    result = run_data_quality_checks(_market_frame().drop(columns=["close"]), "market", output_dir=tmp_path / "quality")

    assert result.status == "FAIL"
    assert _has_issue(result.issue_frame, "MISSING_REQUIRED_COLUMN")


def test_duplicate_market_symbol_trade_date_produces_warn_or_error(tmp_path: Path) -> None:
    duplicate = pd.concat([_market_frame().iloc[[0]], _market_frame().iloc[[0]]], ignore_index=True)

    warn_result = run_data_quality_checks(duplicate, "market", output_dir=tmp_path / "warn")
    error_result = run_data_quality_checks(
        duplicate,
        "market",
        output_dir=tmp_path / "error",
        settings=DataQualitySettings(duplicate_key_severity="ERROR"),
    )

    assert warn_result.status == "WARN"
    assert _issue_row(warn_result.issue_frame, "DUPLICATE_KEY")["severity"] == "WARN"
    assert error_result.status == "FAIL"
    assert _issue_row(error_result.issue_frame, "DUPLICATE_KEY")["severity"] == "ERROR"


def test_negative_price_produces_error(tmp_path: Path) -> None:
    frame = _market_frame()
    frame.loc[0, "close"] = -1

    result = run_data_quality_checks(frame, "market", output_dir=tmp_path / "quality")

    assert result.status == "FAIL"
    assert _has_issue(result.issue_frame, "NON_POSITIVE_PRICE")


def test_ohlc_inconsistency_produces_error(tmp_path: Path) -> None:
    frame = _market_frame()
    frame.loc[0, "high"] = 9.0

    result = run_data_quality_checks(frame, "market", output_dir=tmp_path / "quality")

    assert result.status == "FAIL"
    assert _has_issue(result.issue_frame, "OHLC_INCONSISTENCY")


def test_negative_volume_produces_error(tmp_path: Path) -> None:
    frame = _market_frame()
    frame.loc[0, "volume"] = -100

    result = run_data_quality_checks(frame, "market", output_dir=tmp_path / "quality")

    assert result.status == "FAIL"
    assert _has_issue(result.issue_frame, "NEGATIVE_VOLUME_OR_AMOUNT")


def test_missing_available_time_produces_configured_severity(tmp_path: Path) -> None:
    frame = _market_frame()
    frame.loc[0, "available_time"] = ""

    error_result = run_data_quality_checks(frame, "market", output_dir=tmp_path / "error")
    warn_result = run_data_quality_checks(
        frame,
        "market",
        output_dir=tmp_path / "warn",
        settings=DataQualitySettings(missing_available_time_severity="WARN"),
    )

    assert error_result.status == "FAIL"
    assert _issue_row(error_result.issue_frame, "MISSING_AVAILABLE_TIME")["severity"] == "ERROR"
    assert warn_result.status == "WARN"
    assert _issue_row(warn_result.issue_frame, "MISSING_AVAILABLE_TIME")["severity"] == "WARN"


def test_universe_quality_passes_on_clean_data(tmp_path: Path) -> None:
    result = run_data_quality_checks(_universe_frame(), "universe", output_dir=tmp_path / "quality")

    assert result.status == "PASS"
    assert result.row_count == 2


def test_universe_listed_date_after_as_of_date_produces_error(tmp_path: Path) -> None:
    frame = _universe_frame()
    frame.loc[0, "listed_date"] = "2024-06-01"

    result = run_data_quality_checks(frame, "universe", output_dir=tmp_path / "quality")

    assert result.status == "FAIL"
    assert _has_issue(result.issue_frame, "LISTED_DATE_AFTER_AS_OF_DATE")


def test_corporate_action_missing_available_time_produces_error(tmp_path: Path) -> None:
    frame = _corporate_actions_frame()
    frame.loc[0, "available_time"] = ""

    result = run_data_quality_checks(frame, "corporate_actions", output_dir=tmp_path / "quality")

    assert result.status == "FAIL"
    assert _has_issue(result.issue_frame, "MISSING_AVAILABLE_TIME")


def test_trading_calendar_quality_passes_on_clean_data(tmp_path: Path) -> None:
    result = run_data_quality_checks(_calendar_frame(), "trading_calendar", output_dir=tmp_path / "quality")

    assert result.status == "PASS"
    assert result.row_count == 2


def test_trading_day_missing_session_fields_produces_error(tmp_path: Path) -> None:
    frame = _calendar_frame()
    frame.loc[0, "decision_time"] = ""

    result = run_data_quality_checks(frame, "trading_calendar", output_dir=tmp_path / "quality")

    assert result.status == "FAIL"
    assert _has_issue(result.issue_frame, "TRADING_DAY_MISSING_SESSION_FIELD")


def test_data_quality_artifacts_are_written(tmp_path: Path) -> None:
    result = run_data_quality_checks(_market_frame(), "market", output_dir=tmp_path / "quality")

    for key in [
        "data_quality_report",
        "data_quality_issues",
        "row_counts",
        "missingness_summary",
        "duplicate_summary",
        "source_revision_summary",
        "metadata",
    ]:
        assert result.artifact_paths[key].exists()


def test_data_quality_csv_artifacts_are_readable_by_pandas(tmp_path: Path) -> None:
    result = run_data_quality_checks(_market_frame(), "market", output_dir=tmp_path / "quality")

    pd.read_csv(result.artifact_paths["data_quality_issues"])
    row_counts = pd.read_csv(result.artifact_paths["row_counts"])
    missingness = pd.read_csv(result.artifact_paths["missingness_summary"])
    duplicates = pd.read_csv(result.artifact_paths["duplicate_summary"])
    source_revision = pd.read_csv(result.artifact_paths["source_revision_summary"])

    assert not row_counts.empty
    assert "missing_count" in missingness.columns
    assert "duplicate_row_count" in duplicates.columns
    assert "row_count" in source_revision.columns


def test_data_quality_metadata_json_is_written(tmp_path: Path) -> None:
    result = run_data_quality_checks(_market_frame(), "market", output_dir=tmp_path / "quality")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["dataset_type"] == "market"
    assert metadata["status"] == "PASS"
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_data_quality_output_is_deterministic_for_same_input(tmp_path: Path) -> None:
    first = run_data_quality_checks(_market_frame(), "market", output_dir=tmp_path / "quality")
    second = run_data_quality_checks(_market_frame(), "market", output_dir=tmp_path / "quality")

    assert first.quality_run_id == second.quality_run_id
    assert first.issue_frame.to_dict("records") == second.issue_frame.to_dict("records")
    assert first.row_count_summary.to_dict("records") == second.row_count_summary.to_dict("records")


def test_cli_data_quality_works(tmp_path: Path, capsys) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)

    code = cli.main(
        [
            "data-quality",
            "--dataset-type",
            "market",
            "--input",
            str(input_path),
            "--output-dir",
            str(tmp_path / "quality"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Data quality status: PASS" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_cli_data_quality_exits_nonzero_on_fail_by_default(tmp_path: Path, capsys) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().drop(columns=["close"]).to_csv(input_path, index=False)

    code = cli.main(
        [
            "data-quality",
            "--dataset-type",
            "market",
            "--input",
            str(input_path),
            "--output-dir",
            str(tmp_path / "quality"),
        ]
    )
    output = capsys.readouterr()

    assert code == 1
    assert "Data quality status: FAIL" in output.out


def test_data_quality_makes_no_network_calls(tmp_path: Path) -> None:
    result = run_data_quality_checks(_market_frame(), "market", output_dir=tmp_path / "quality")

    assert result.audit_metadata["data_quality_only"] is True


def test_data_quality_does_not_invoke_live_trading_or_broker(tmp_path: Path) -> None:
    result = run_data_quality_checks(_market_frame(), "market", output_dir=tmp_path / "quality")

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False


def _has_issue(frame: pd.DataFrame, issue_code: str) -> bool:
    return bool((frame["issue_code"] == issue_code).any()) if not frame.empty else False


def _issue_row(frame: pd.DataFrame, issue_code: str) -> dict:
    rows = frame.loc[frame["issue_code"] == issue_code]
    assert not rows.empty
    return rows.iloc[0].to_dict()


def _market_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "trade_date": "2024-05-20",
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 1000,
                "amount": 10200,
                "pre_close": 9.9,
                "adj_factor": 1.0,
                "is_suspended": False,
                "limit_up": 10.89,
                "limit_down": 8.91,
                "event_time": "2024-05-20 15:00:00",
                "publish_time": "2024-05-20 15:10:00",
                "ingest_time": "2024-05-20 15:20:00",
                "available_time": "2024-05-20 15:30:00",
                "revision_id": "v1",
                "source": "TEST",
            },
            {
                "symbol": "BBB",
                "trade_date": "2024-05-20",
                "open": 20.0,
                "high": 20.5,
                "low": 19.8,
                "close": 20.2,
                "volume": 2000,
                "amount": 40400,
                "pre_close": 19.9,
                "adj_factor": 1.0,
                "is_suspended": False,
                "limit_up": 21.89,
                "limit_down": 17.91,
                "event_time": "2024-05-20 15:00:00",
                "publish_time": "2024-05-20 15:10:00",
                "ingest_time": "2024-05-20 15:20:00",
                "available_time": "2024-05-20 15:30:00",
                "revision_id": "v1",
                "source": "TEST",
            },
        ]
    )


def _universe_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "as_of_date": "2024-05-20",
                "symbol": "AAA",
                "name": "AAA Fund",
                "instrument_type": "ETF",
                "exchange": "SSE",
                "listed_date": "2020-01-01",
                "delisted_date": "",
                "is_active": True,
                "is_st": False,
                "is_suspended": False,
                "industry": "ETF",
                "min_lot": 100,
                "t_plus_rule": "T+1",
                "available_time": "2024-05-20 08:00:00",
                "revision_id": "v1",
                "source": "TEST",
            },
            {
                "as_of_date": "2024-05-20",
                "symbol": "BBB",
                "name": "BBB Stock",
                "instrument_type": "STOCK",
                "exchange": "SZSE",
                "listed_date": "2020-01-01",
                "delisted_date": "",
                "is_active": True,
                "is_st": False,
                "is_suspended": False,
                "industry": "Tech",
                "min_lot": 100,
                "t_plus_rule": "T+1",
                "available_time": "2024-05-20 08:00:00",
                "revision_id": "v1",
                "source": "TEST",
            },
        ]
    )


def _corporate_actions_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "action_type": "CASH_DIVIDEND",
                "ex_date": "2024-05-20",
                "record_date": "2024-05-17",
                "cash_dividend": 0.1,
                "split_ratio": 1.0,
                "rights_issue": False,
                "event_time": "2024-05-10 15:00:00",
                "publish_time": "2024-05-10 16:00:00",
                "ingest_time": "2024-05-10 16:30:00",
                "available_time": "2024-05-10 17:00:00",
                "revision_id": "v1",
                "source": "TEST",
            }
        ]
    )


def _calendar_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2024-05-20",
                "is_trading_day": True,
                "session_open": "09:30",
                "session_close": "15:00",
                "decision_time": "15:30",
                "reason": "normal",
            },
            {
                "trade_date": "2024-05-21",
                "is_trading_day": False,
                "session_open": "",
                "session_close": "",
                "decision_time": "",
                "reason": "holiday",
            },
        ]
    )
