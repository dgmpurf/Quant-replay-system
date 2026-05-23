import json
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.current_candidates import generate_current_candidates
from quant_replay_system.data_pipeline import DataPipelineDatasetRequest, run_data_source_ingestion_pipeline
from quant_replay_system.universe_overlay import (
    load_universe_overlay_csv,
    merge_universe_overlay,
    run_universe_overlay,
    validate_universe_overlay,
)


DECISION_DATE = "2024-03-01"


def test_overlay_loads_and_validates_canonical_columns(tmp_path: Path) -> None:
    overlay_path = tmp_path / "overlay.csv"
    _overlay_frame().to_csv(overlay_path, index=False)

    overlay = load_universe_overlay_csv(overlay_path, label="overlay")
    validate_universe_overlay(overlay)

    assert list(overlay.columns) == _universe_columns()
    assert overlay["symbol"].tolist() == ["510300", "159915"]


def test_overlay_rejects_missing_symbol(tmp_path: Path) -> None:
    overlay = _overlay_frame()
    overlay.loc[0, "symbol"] = ""

    with pytest.raises(ValueError, match="symbol is required"):
        validate_universe_overlay(overlay)


def test_overlay_rejects_duplicate_overlay_symbols(tmp_path: Path) -> None:
    overlay = pd.concat([_overlay_frame().iloc[[0]], _overlay_frame().iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="duplicate overlay symbols"):
        validate_universe_overlay(overlay)


def test_overlay_preserves_etf_and_stock_symbol_strings(tmp_path: Path) -> None:
    base_path = tmp_path / "base.csv"
    overlay_path = tmp_path / "overlay.csv"
    _base_universe_frame().to_csv(base_path, index=False)
    _overlay_frame().to_csv(overlay_path, index=False)

    result = run_universe_overlay(base_path, overlay_path, settings=_settings(tmp_path))
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})

    assert {"000001", "510300", "159915"}.issubset(set(exported["symbol"]))
    assert exported.loc[exported["symbol"] == "510300", "instrument_type"].iloc[0] == "ETF"


def test_overlay_adds_etf_rows_to_stock_only_base_universe(tmp_path: Path) -> None:
    result = run_universe_overlay(
        _write_csv(tmp_path / "base.csv", _base_universe_frame()),
        _write_csv(tmp_path / "overlay.csv", _overlay_frame()),
        settings=_settings(tmp_path),
    )

    assert result.base_row_count == 1
    assert result.overlay_row_count == 2
    assert result.row_count == 3
    assert result.added_symbols == ["159915", "510300"]
    assert result.overridden_symbols == []


def test_merge_output_contains_base_and_added_etf_rows() -> None:
    merged = merge_universe_overlay(_base_universe_frame(), _overlay_frame())["merged"]

    assert set(merged["symbol"]) == {"000001", "510300", "159915"}
    assert dict(zip(merged["symbol"], merged["instrument_type"]))["510300"] == "ETF"


def test_overlay_rejects_existing_symbol_unless_override_allowed() -> None:
    overlay = pd.DataFrame([_universe_row("000001", "Reviewed Bank", "STOCK")])

    with pytest.raises(ValueError, match="already exist"):
        merge_universe_overlay(_base_universe_frame(), overlay)

    result = merge_universe_overlay(_base_universe_frame(), overlay, allow_override_existing=True)

    assert result["overridden_symbols"] == ["000001"]
    assert result["merged"].loc[result["merged"]["symbol"] == "000001", "name"].iloc[0] == "Reviewed Bank"


def test_data_pipeline_can_ingest_merged_universe(tmp_path: Path) -> None:
    overlay_result = run_universe_overlay(
        _write_csv(tmp_path / "base.csv", _base_universe_frame()),
        _write_csv(tmp_path / "overlay.csv", _overlay_frame()),
        settings=_settings(tmp_path),
    )

    pipeline = run_data_source_ingestion_pipeline(
        [
            DataPipelineDatasetRequest(
                dataset_type="universe",
                source="LOCAL_CSV",
                input_path=overlay_result.artifact_paths["raw_data"],
            )
        ],
        config=_settings(tmp_path),
        run_data_quality=False,
    )
    processed = pd.read_csv(pipeline.processed_paths["universe"], dtype={"symbol": str})

    assert pipeline.status == "PASS"
    assert {"000001", "510300", "159915"}.issubset(set(processed["symbol"]))


def test_overlay_output_normalizes_mixed_date_formats_for_ingestion(tmp_path: Path) -> None:
    base = _base_universe_frame()
    base["as_of_date"] = f"{DECISION_DATE} 00:00:00"
    overlay = _overlay_frame()
    overlay["as_of_date"] = DECISION_DATE
    result = run_universe_overlay(
        _write_csv(tmp_path / "base.csv", base),
        _write_csv(tmp_path / "overlay.csv", overlay),
        settings=_settings(tmp_path),
    )

    pipeline = run_data_source_ingestion_pipeline(
        [
            DataPipelineDatasetRequest(
                dataset_type="universe",
                source="LOCAL_CSV",
                input_path=result.artifact_paths["raw_data"],
            )
        ],
        config=_settings(tmp_path),
        run_data_quality=False,
    )
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str}, keep_default_na=False)

    assert pipeline.status == "PASS"
    assert exported["as_of_date"].nunique() == 1
    assert exported["as_of_date"].iloc[0] == f"{DECISION_DATE} 00:00:00"


def test_current_candidates_can_join_510300_with_merged_universe(tmp_path: Path) -> None:
    overlay_result = run_universe_overlay(
        _write_csv(tmp_path / "base.csv", _base_universe_frame()),
        _write_csv(tmp_path / "overlay.csv", _overlay_frame()),
        settings=_settings(tmp_path),
    )
    market_path = _write_csv(tmp_path / "market.csv", _market_frame("510300"))
    calendar_path = _write_csv(tmp_path / "calendar.csv", _calendar_frame())

    pipeline = run_data_source_ingestion_pipeline(
        [
            {"dataset_type": "market", "source": "LOCAL_CSV", "input_path": market_path},
            {"dataset_type": "universe", "source": "LOCAL_CSV", "input_path": overlay_result.artifact_paths["raw_data"]},
            {"dataset_type": "trading_calendar", "source": "LOCAL_CSV", "input_path": calendar_path},
        ],
        config=_settings(tmp_path),
        run_data_quality=False,
        build_snapshot_manifest=True,
    )
    result = generate_current_candidates(
        DECISION_DATE,
        universe_name="etf_core",
        top_n=2,
        config=_settings(tmp_path),
        snapshot_manifest_path=pipeline.snapshot_manifest_path,
        enable_snapshot_preflight=False,
    )

    assert result.factor_dataset_row_count == 1
    assert result.factor_dataset["symbol"].tolist() == ["510300"]
    assert result.audit_metadata["market_universe_intersection_count"] == 1


def test_cli_universe_overlay_works(tmp_path: Path, capsys) -> None:
    base_path = _write_csv(tmp_path / "base.csv", _base_universe_frame())
    overlay_path = _write_csv(tmp_path / "overlay.csv", _overlay_frame())

    code = cli.main(
        [
            "universe-overlay",
            "--base-universe",
            str(base_path),
            "--overlay",
            str(overlay_path),
            "--output-dir",
            str(tmp_path / "overlay_output"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "merged_universe_path:" in output.out
    assert "added_symbol_count: 2" in output.out
    assert "report_path:" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_overlay_artifacts_and_metadata_are_written(tmp_path: Path) -> None:
    result = run_universe_overlay(
        _write_csv(tmp_path / "base.csv", _base_universe_frame()),
        _write_csv(tmp_path / "overlay.csv", _overlay_frame()),
        settings=_settings(tmp_path),
    )
    metadata = json.loads(result.artifact_paths["overlay_metadata"].read_text(encoding="utf-8"))

    assert result.artifact_paths["raw_data"].exists()
    assert result.artifact_paths["universe_overlay_report"].exists()
    assert metadata["added_symbol_count"] == 2
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_no_live_trading_or_network_calls_are_invoked(tmp_path: Path) -> None:
    result = run_universe_overlay(
        _write_csv(tmp_path / "base.csv", _base_universe_frame()),
        _write_csv(tmp_path / "overlay.csv", _overlay_frame()),
        settings=_settings(tmp_path),
    )

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["network_api_calls_used_in_tests"] is False


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "universe_overlay": settings.universe_overlay.model_copy(
                update={"output_dir": tmp_path / "raw" / "LOCAL_CSV" / "universe_overlay"}
            ),
            "data_pipeline": settings.data_pipeline.model_copy(
                update={
                    "output_dir": tmp_path / "reports" / "data_pipeline",
                    "raw_output_dir": tmp_path / "raw",
                    "processed_output_dir": tmp_path / "processed",
                    "snapshot_output_dir": tmp_path / "snapshots",
                }
            ),
            "current_candidates": settings.current_candidates.model_copy(
                update={
                    "output_dir": tmp_path / "reports" / "current_candidates",
                    "min_action": "NO_TRADE",
                    "min_final_score": None,
                    "default_top_n": 2,
                }
            ),
        }
    )


def _write_csv(path: Path, frame: pd.DataFrame) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path


def _base_universe_frame() -> pd.DataFrame:
    return pd.DataFrame([_universe_row("000001", "Ping An Bank", "STOCK")])


def _overlay_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _universe_row("510300", "CSI 300 ETF", "ETF"),
            _universe_row("159915", "ChiNext ETF", "ETF"),
        ]
    )


def _universe_row(symbol: str, name: str, instrument_type: str) -> dict:
    return {
        "as_of_date": DECISION_DATE,
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
        "available_time": f"{DECISION_DATE} 08:00:00",
        "revision_id": "manual-overlay-v1",
        "source": "MANUAL_ETF_OVERLAY" if instrument_type == "ETF" else "BASE_UNIVERSE",
    }


def _market_frame(symbol: str) -> pd.DataFrame:
    rows = []
    previous_close = None
    for idx, trade_date in enumerate(pd.bdate_range("2024-01-02", DECISION_DATE)):
        close = 10 + idx * 0.1
        rows.append(
            {
                "symbol": symbol,
                "trade_date": trade_date.date().isoformat(),
                "open": close - 0.05,
                "high": close + 0.1,
                "low": close - 0.1,
                "close": close,
                "volume": 1_000_000 + idx,
                "amount": 10_000_000 + idx,
                "pre_close": previous_close if previous_close is not None else close - 0.1,
                "adj_factor": 1.0,
                "is_suspended": False,
                "limit_up": close * 1.1,
                "limit_down": close * 0.9,
                "event_time": f"{trade_date.date()} 15:00:00",
                "publish_time": f"{trade_date.date()} 15:10:00",
                "ingest_time": f"{trade_date.date()} 15:20:00",
                "available_time": f"{trade_date.date()} 15:30:00",
                "revision_id": "market-v1",
                "source": "TEST",
            }
        )
        previous_close = close
    return pd.DataFrame(rows)


def _calendar_frame() -> pd.DataFrame:
    rows = []
    for trade_date in pd.bdate_range("2024-01-02", DECISION_DATE):
        rows.append(
            {
                "trade_date": trade_date.date().isoformat(),
                "is_trading_day": True,
                "session_open": "09:30",
                "session_close": "15:00",
                "decision_time": "15:30",
                "reason": "normal",
            }
        )
    return pd.DataFrame(rows)


def _universe_columns() -> list[str]:
    return [
        "as_of_date",
        "symbol",
        "name",
        "instrument_type",
        "exchange",
        "listed_date",
        "delisted_date",
        "is_active",
        "is_st",
        "is_suspended",
        "industry",
        "min_lot",
        "t_plus_rule",
        "available_time",
        "revision_id",
        "source",
    ]
