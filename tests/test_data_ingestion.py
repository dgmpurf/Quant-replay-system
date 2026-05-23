import json
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.config import DataIngestionSettings
from quant_replay_system.data_ingestion import (
    build_processed_snapshot,
    ingest_benchmark_data_csv,
    ingest_corporate_actions_csv,
    ingest_market_data_csv,
    ingest_trading_calendar_csv,
    ingest_universe_snapshot_csv,
)


def test_market_csv_ingestion_succeeds_with_complete_schema(tmp_path: Path) -> None:
    path = tmp_path / "market.csv"
    _market_frame().to_csv(path, index=False)

    result = ingest_market_data_csv(path, settings=_settings(tmp_path))

    assert result.row_count == 2
    assert result.validation.valid is True
    assert list(result.cleaned_data["symbol"]) == ["AAA", "BBB"]
    assert "available_time" in result.cleaned_data.columns


def test_missing_required_market_column_fails(tmp_path: Path) -> None:
    path = tmp_path / "market.csv"
    _market_frame().drop(columns=["close"]).to_csv(path, index=False)

    with pytest.raises(ValueError, match="MISSING_REQUIRED_COLUMN"):
        ingest_market_data_csv(path, settings=_settings(tmp_path))


def test_missing_available_time_defaults_when_enabled(tmp_path: Path) -> None:
    path = tmp_path / "market.csv"
    _market_frame().drop(columns=["available_time", "source", "revision_id"]).to_csv(path, index=False)

    result = ingest_market_data_csv(path, settings=_settings(tmp_path))

    assert result.validation.warning_count == 1
    assert set(result.cleaned_data["available_time"]) == {pd.Timestamp("2024-05-20 15:30:00")}
    assert set(result.cleaned_data["source"]) == {"LOCAL_CSV"}
    assert set(result.cleaned_data["revision_id"]) == {"v1"}


def test_missing_available_time_fails_when_defaulting_disabled(tmp_path: Path) -> None:
    path = tmp_path / "market.csv"
    _market_frame().drop(columns=["available_time"]).to_csv(path, index=False)

    settings = _settings(tmp_path, allow_default_available_time=False)
    with pytest.raises(ValueError, match="MISSING_AVAILABLE_TIME"):
        ingest_market_data_csv(path, settings=settings)


def test_negative_price_fails(tmp_path: Path) -> None:
    path = tmp_path / "market.csv"
    frame = _market_frame()
    frame.loc[0, "open"] = -1.0
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="NEGATIVE_PRICE"):
        ingest_market_data_csv(path, settings=_settings(tmp_path))


def test_negative_volume_fails(tmp_path: Path) -> None:
    path = tmp_path / "market.csv"
    frame = _market_frame()
    frame.loc[0, "volume"] = -10
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="NEGATIVE_VOLUME_OR_AMOUNT"):
        ingest_market_data_csv(path, settings=_settings(tmp_path))


def test_duplicate_symbol_trade_date_warns_or_fails_by_config(tmp_path: Path) -> None:
    path = tmp_path / "market.csv"
    duplicate = pd.concat([_market_frame().iloc[[0]], _market_frame().iloc[[0]]], ignore_index=True)
    duplicate.to_csv(path, index=False)

    warn_result = ingest_market_data_csv(path, settings=_settings(tmp_path))
    assert warn_result.validation.warning_count == 1
    assert "DUPLICATE_KEY" in set(warn_result.validation.validation_report["issue_code"])

    with pytest.raises(ValueError, match="DUPLICATE_KEY"):
        ingest_market_data_csv(path, settings=_settings(tmp_path, duplicate_key_severity="ERROR"))


def test_universe_snapshot_ingestion_succeeds(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    _universe_frame().to_csv(path, index=False)

    result = ingest_universe_snapshot_csv(path, settings=_settings(tmp_path))

    assert result.row_count == 3
    assert result.validation.valid is True
    assert set(result.cleaned_data["symbol"]) == {"AAA", "BBB", "CCC"}


def test_market_ingestion_preserves_numeric_leading_zero_symbol(tmp_path: Path) -> None:
    path = tmp_path / "market.csv"
    frame = _market_frame().iloc[[0]].copy()
    frame["symbol"] = "000001"
    frame.to_csv(path, index=False)

    result = ingest_market_data_csv(path, settings=_settings(tmp_path))

    assert result.cleaned_data["symbol"].tolist() == ["000001"]


def test_market_ingestion_pads_numeric_symbol_when_source_csv_was_stripped(tmp_path: Path) -> None:
    path = tmp_path / "market.csv"
    frame = _market_frame().iloc[[0]].copy()
    frame["symbol"] = 1
    frame.to_csv(path, index=False)

    result = ingest_market_data_csv(path, settings=_settings(tmp_path))

    assert result.cleaned_data["symbol"].tolist() == ["000001"]


def test_universe_ingestion_preserves_leading_zero_and_etf_symbols(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    frame = pd.DataFrame(
        [
            _reviewed_universe_row("000001", "Ping An Bank", "STOCK"),
            _reviewed_universe_row("510300", "CSI 300 ETF", "ETF"),
            _reviewed_universe_row("159915", "ChiNext ETF", "ETF"),
        ]
    )
    frame.to_csv(path, index=False)

    result = ingest_universe_snapshot_csv(path, settings=_settings(tmp_path))

    assert result.cleaned_data["symbol"].tolist() == ["000001", "159915", "510300"]
    assert dict(zip(result.cleaned_data["symbol"], result.cleaned_data["instrument_type"])) == {
        "000001": "STOCK",
        "159915": "ETF",
        "510300": "ETF",
    }


def test_universe_ingestion_succeeds_with_listed_date_blank(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    frame = _universe_frame()
    frame.loc[0, "listed_date"] = ""
    frame.to_csv(path, index=False)

    result = ingest_universe_snapshot_csv(path, settings=_settings(tmp_path))

    assert result.validation.valid is True
    assert "listed_date" in result.cleaned_data.columns
    assert pd.isna(result.cleaned_data.loc[result.cleaned_data["symbol"] == "AAA", "listed_date"].iloc[0])


def test_universe_ingestion_succeeds_with_listed_date_nan_token(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    frame = _universe_frame()
    frame.loc[0, "listed_date"] = "NaN"
    frame.to_csv(path, index=False)

    result = ingest_universe_snapshot_csv(path, settings=_settings(tmp_path))

    assert result.validation.valid is True
    assert pd.isna(result.cleaned_data.loc[result.cleaned_data["symbol"] == "AAA", "listed_date"].iloc[0])


def test_universe_ingestion_succeeds_with_listed_date_nat_token(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    frame = _universe_frame()
    frame.loc[0, "listed_date"] = "NaT"
    frame.to_csv(path, index=False)

    result = ingest_universe_snapshot_csv(path, settings=_settings(tmp_path))

    assert result.validation.valid is True
    assert pd.isna(result.cleaned_data.loc[result.cleaned_data["symbol"] == "AAA", "listed_date"].iloc[0])


def test_universe_ingestion_succeeds_with_listed_date_dash_token(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    frame = _universe_frame()
    frame.loc[0, "listed_date"] = "--"
    frame.to_csv(path, index=False)

    result = ingest_universe_snapshot_csv(path, settings=_settings(tmp_path))

    assert result.validation.valid is True
    assert pd.isna(result.cleaned_data.loc[result.cleaned_data["symbol"] == "AAA", "listed_date"].iloc[0])


def test_universe_ingestion_fails_with_invalid_non_empty_listed_date(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    frame = _universe_frame()
    frame.loc[0, "listed_date"] = "not-a-date"
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="INVALID_DATE"):
        ingest_universe_snapshot_csv(path, settings=_settings(tmp_path))


def test_universe_ingestion_fails_when_listed_date_after_as_of_date(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    frame = _universe_frame()
    frame.loc[0, "listed_date"] = "2024-06-01"
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="LISTED_DATE_AFTER_AS_OF_DATE"):
        ingest_universe_snapshot_csv(path, settings=_settings(tmp_path))


def test_universe_ingestion_succeeds_with_delisted_date_blank(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    frame = _universe_frame()
    frame.loc[0, "delisted_date"] = ""
    frame.to_csv(path, index=False)

    result = ingest_universe_snapshot_csv(path, settings=_settings(tmp_path))

    assert result.validation.valid is True
    assert "delisted_date" in result.cleaned_data.columns
    assert pd.isna(result.cleaned_data.loc[result.cleaned_data["symbol"] == "AAA", "delisted_date"].iloc[0])


def test_universe_ingestion_fails_when_delisted_date_before_listed_date(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    frame = _universe_frame()
    frame.loc[0, "listed_date"] = "2020-01-01"
    frame.loc[0, "delisted_date"] = "2019-12-31"
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="DELISTED_DATE_BEFORE_LISTED_DATE"):
        ingest_universe_snapshot_csv(path, settings=_settings(tmp_path))


def test_universe_inactive_st_suspended_fields_are_preserved(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    _universe_frame().to_csv(path, index=False)

    result = ingest_universe_snapshot_csv(path, settings=_settings(tmp_path))
    by_symbol = result.cleaned_data.set_index("symbol")

    assert bool(by_symbol.loc["BBB", "is_st"]) is True
    assert bool(by_symbol.loc["CCC", "is_suspended"]) is True
    assert bool(by_symbol.loc["CCC", "is_active"]) is False


def test_corporate_actions_missing_available_time_fails_by_default(tmp_path: Path) -> None:
    path = tmp_path / "actions.csv"
    _corporate_actions_frame().drop(columns=["available_time"]).to_csv(path, index=False)

    with pytest.raises(ValueError, match="MISSING_AVAILABLE_TIME"):
        ingest_corporate_actions_csv(path, settings=_settings(tmp_path))


def test_trading_calendar_ingestion_succeeds(tmp_path: Path) -> None:
    path = tmp_path / "calendar.csv"
    _calendar_frame().to_csv(path, index=False)

    result = ingest_trading_calendar_csv(path, settings=_settings(tmp_path))

    assert result.row_count == 2
    assert result.validation.valid is True
    assert list(result.cleaned_data.columns) == [
        "trade_date",
        "is_trading_day",
        "session_open",
        "session_close",
        "decision_time",
        "reason",
    ]


def test_processed_artifact_csv_is_written_and_readable(tmp_path: Path) -> None:
    path = tmp_path / "market.csv"
    _market_frame().to_csv(path, index=False)

    result = ingest_market_data_csv(path, settings=_settings(tmp_path))
    cleaned = pd.read_csv(result.artifact_paths["cleaned_csv"])

    assert len(cleaned) == 2
    assert "available_time" in cleaned.columns


def test_validation_report_csv_is_written_and_readable(tmp_path: Path) -> None:
    path = tmp_path / "market.csv"
    _market_frame().drop(columns=["available_time"]).to_csv(path, index=False)

    result = ingest_market_data_csv(path, settings=_settings(tmp_path))
    report = pd.read_csv(result.artifact_paths["validation_report"])

    assert "issue_code" in report.columns
    assert "DEFAULT_AVAILABLE_TIME_ASSIGNED" in set(report["issue_code"])


def test_metadata_json_is_written(tmp_path: Path) -> None:
    path = tmp_path / "market.csv"
    _market_frame().to_csv(path, index=False)

    result = ingest_market_data_csv(path, settings=_settings(tmp_path))
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["dataset_type"] == "market"
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_snapshot_manifest_is_written(tmp_path: Path) -> None:
    path = tmp_path / "market.csv"
    _market_frame().to_csv(path, index=False)
    market = ingest_market_data_csv(path, settings=_settings(tmp_path))

    snapshot = build_processed_snapshot("daily_local", {"market": market}, settings=_settings(tmp_path))
    manifest = json.loads(snapshot.manifest_path.read_text(encoding="utf-8"))

    assert snapshot.manifest_path.exists()
    assert manifest["snapshot_name"] == "daily_local"
    assert manifest["row_counts"]["market"] == 2


def test_ingestion_is_deterministic_for_same_input(tmp_path: Path) -> None:
    path = tmp_path / "market.csv"
    _market_frame().to_csv(path, index=False)

    first = ingest_market_data_csv(path, settings=_settings(tmp_path))
    second = ingest_market_data_csv(path, settings=_settings(tmp_path))

    assert first.cleaned_data.to_dict("records") == second.cleaned_data.to_dict("records")
    assert first.artifact_paths == second.artifact_paths
    assert first.validation.validation_report.to_dict("records") == second.validation.validation_report.to_dict("records")


def test_benchmark_ingestion_uses_market_schema(tmp_path: Path) -> None:
    path = tmp_path / "benchmark.csv"
    frame = _market_frame()
    frame["symbol"] = "CSI300"
    frame.to_csv(path, index=False)

    result = ingest_benchmark_data_csv(path, settings=_settings(tmp_path))

    assert result.dataset_type == "benchmark"
    assert set(result.cleaned_data["symbol"]) == {"CSI300"}


def test_no_network_calls_are_made(tmp_path: Path) -> None:
    path = tmp_path / "market.csv"
    _market_frame().to_csv(path, index=False)

    result = ingest_market_data_csv(path, settings=_settings(tmp_path))

    assert result.audit_metadata["data_ingestion_only"] is True


def test_no_live_trading_or_broker_integration_is_invoked(tmp_path: Path) -> None:
    path = tmp_path / "market.csv"
    _market_frame().to_csv(path, index=False)

    result = ingest_market_data_csv(path, settings=_settings(tmp_path))

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False


def _settings(tmp_path: Path, **overrides) -> DataIngestionSettings:
    payload = {
        "output_dir": tmp_path / "processed",
        "snapshot_dir": tmp_path / "snapshots",
        "write_artifacts": True,
    }
    payload.update(overrides)
    return DataIngestionSettings(**payload)


def _market_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "aaa",
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
                "symbol": "bbb",
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
                "symbol": "aaa",
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
                "symbol": "bbb",
                "name": "BBB Stock",
                "instrument_type": "STOCK",
                "exchange": "SZSE",
                "listed_date": "2020-01-01",
                "delisted_date": "",
                "is_active": True,
                "is_st": True,
                "is_suspended": False,
                "industry": "Tech",
                "min_lot": 100,
                "t_plus_rule": "T+1",
                "available_time": "2024-05-20 08:00:00",
                "revision_id": "v1",
                "source": "TEST",
            },
            {
                "as_of_date": "2024-05-20",
                "symbol": "ccc",
                "name": "CCC Stock",
                "instrument_type": "STOCK",
                "exchange": "SSE",
                "listed_date": "2020-01-01",
                "delisted_date": "",
                "is_active": False,
                "is_st": False,
                "is_suspended": True,
                "industry": "Finance",
                "min_lot": 100,
                "t_plus_rule": "T+1",
                "available_time": "2024-05-20 08:00:00",
                "revision_id": "v1",
                "source": "TEST",
            },
        ]
    )


def _reviewed_universe_row(symbol: str, name: str, instrument_type: str) -> dict:
    return {
        "as_of_date": "2024-05-20",
        "symbol": symbol,
        "name": name,
        "instrument_type": instrument_type,
        "exchange": "SSE" if symbol.startswith("5") else "SZSE",
        "listed_date": "",
        "delisted_date": "",
        "is_active": True,
        "is_st": False,
        "is_suspended": False,
        "industry": instrument_type,
        "min_lot": 100,
        "t_plus_rule": "T+1",
        "available_time": "2024-05-20 08:00:00",
        "revision_id": "v1",
        "source": "TEST",
    }


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
