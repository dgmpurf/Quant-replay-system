import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quant_replay_system import cli
from quant_replay_system.calendar import TradingCalendar
from quant_replay_system.config import load_settings
from quant_replay_system.current_candidates import (
    CurrentCandidateResult,
    generate_current_candidate_run_id,
    generate_current_candidates,
)
from quant_replay_system.daily_paper_runner import load_candidates_for_paper_trading, run_daily_paper_trading
from quant_replay_system.snapshot_quality_preflight import SnapshotQualityPreflightError


DECISION_DATE = pd.Timestamp("2024-03-01")
DECISION_TIME = pd.Timestamp("2024-03-01 15:30:00")


def test_generate_current_candidates_returns_structured_result(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert isinstance(result, CurrentCandidateResult)
    assert result.decision_date == DECISION_DATE
    assert result.decision_time == DECISION_TIME
    assert result.universe_name == "unit_test"
    assert isinstance(result.audit_metadata, dict)


def test_factor_dataset_is_built(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert result.factor_dataset_row_count == len(result.factor_dataset)
    assert result.factor_dataset_row_count > 0
    assert {"decision_date", "symbol", "latest_market_available_time"}.issubset(result.factor_dataset.columns)


def test_scored_dataset_is_built(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert result.scored_dataset_row_count == len(result.scored_dataset)
    assert {"final_score", "score_action", "score_reason", "score_breakdown"}.issubset(result.scored_dataset.columns)


def test_candidates_are_selected_and_sorted_by_final_score(tmp_path: Path) -> None:
    result = _run(tmp_path, top_n=2)

    scores = result.candidates["final_score"].tolist()
    assert scores == sorted(scores, reverse=True)
    assert len(result.candidates) <= 2
    assert "current_candidate_run_id" in result.candidates.columns


def test_candidates_csv_is_written(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert result.artifact_paths["candidates"].exists()


def test_current_candidates_report_is_written(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert result.artifact_paths["current_candidates_report"].exists()
    content = result.artifact_paths["current_candidates_report"].read_text(encoding="utf-8")
    assert "## Candidate Table" in content
    assert "No broker or live trading integration was invoked" in content


def test_metadata_json_is_written(tmp_path: Path) -> None:
    result = _run(tmp_path)
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["run_id"] == result.run_id
    assert metadata["row_counts"]["candidates"] == result.candidate_count
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_output_is_deterministic_for_same_inputs(tmp_path: Path) -> None:
    market = _make_market_data(["AAA", "BBB"])
    universe = _make_universe_snapshot(["AAA", "BBB"])
    benchmark = _make_benchmark_data()
    calendar = _make_calendar()
    settings = _settings(tmp_path)

    first = generate_current_candidates(
        DECISION_DATE,
        universe_name="unit_test",
        top_n=2,
        config=settings,
        market_data=market,
        universe_snapshot=universe,
        benchmark_data=benchmark,
        trading_calendar=calendar,
    )
    second = generate_current_candidates(
        DECISION_DATE,
        universe_name="unit_test",
        top_n=2,
        config=settings,
        market_data=market,
        universe_snapshot=universe,
        benchmark_data=benchmark,
        trading_calendar=calendar,
    )

    assert first.run_id == second.run_id
    assert first.artifact_paths["artifact_dir"] == second.artifact_paths["artifact_dir"]
    assert_frame_equal(first.factor_dataset, second.factor_dataset)
    assert_frame_equal(first.scored_dataset, second.scored_dataset)
    assert_frame_equal(first.candidates, second.candidates)


def test_candidates_csv_is_compatible_with_paper_daily_candidate_loading(tmp_path: Path) -> None:
    result = _run(tmp_path)

    loaded = load_candidates_for_paper_trading(candidates_path=result.artifact_paths["candidates"])
    paper_result = run_daily_paper_trading(
        DECISION_DATE,
        candidates_path=result.artifact_paths["candidates"],
        output_dir=tmp_path / "paper",
        config=_settings(tmp_path),
    )

    assert len(loaded) == result.candidate_count
    assert paper_result.decision_count == result.candidate_count
    assert "source_run_id" in paper_result.decisions.columns


def test_snapshot_preflight_runs_when_snapshot_manifest_is_provided(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)
    result = _run(tmp_path, snapshot_manifest_path=manifest)

    assert result.audit_metadata["snapshot_quality_preflight_enabled"] is True
    assert result.snapshot_quality_status == "PASS"
    assert result.snapshot_quality_report_path is not None
    assert result.snapshot_quality_report_path.exists()


def test_current_candidates_run_with_processed_universe_missing_listed_date(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, missing_listed_date=True)

    result = generate_current_candidates(
        DECISION_DATE,
        universe_name="unit_test",
        top_n=2,
        config=_settings(tmp_path),
        snapshot_manifest_path=manifest,
    )

    assert result.factor_dataset_row_count > 0
    assert set(result.factor_dataset["symbol"]) == {"AAA", "BBB"}


def test_current_candidates_can_build_factor_dataset_for_etf_symbol(tmp_path: Path) -> None:
    result = generate_current_candidates(
        DECISION_DATE,
        universe_name="etf_core",
        top_n=2,
        config=_settings(tmp_path),
        market_data=_make_market_data(["510300"]),
        universe_snapshot=_make_universe_snapshot(["510300"]),
        benchmark_data=_make_benchmark_data(),
        trading_calendar=_make_calendar(),
    )

    assert result.factor_dataset_row_count == 1
    assert result.factor_dataset["symbol"].tolist() == ["510300"]
    assert result.audit_metadata["market_universe_intersection_count"] == 1


def test_current_candidates_empty_factor_dataset_reports_symbol_diagnostics(tmp_path: Path) -> None:
    result = generate_current_candidates(
        DECISION_DATE,
        universe_name="etf_core",
        top_n=2,
        config=_settings(tmp_path),
        market_data=_make_market_data(["510300"]),
        universe_snapshot=_make_universe_snapshot(["000001"]),
        benchmark_data=None,
        trading_calendar=_make_calendar(),
    )

    assert result.factor_dataset_row_count == 0
    assert result.audit_metadata["market_symbol_count"] == 1
    assert result.audit_metadata["universe_symbol_count"] == 1
    assert result.audit_metadata["market_universe_intersection_count"] == 0
    assert result.audit_metadata["missing_market_symbols_sample"] == ["510300"]
    assert any("Factor dataset is empty" in warning for warning in result.warnings)


def test_snapshot_preflight_fail_blocks_when_configured(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, bad_market=True)

    with pytest.raises(SnapshotQualityPreflightError, match="blocked generate_current_candidates: status=FAIL"):
        _run(tmp_path, snapshot_manifest_path=manifest)


def test_snapshot_preflight_warn_continues_when_allowed(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, bad_benchmark=True)
    result = _run(tmp_path, snapshot_manifest_path=manifest)

    assert result.snapshot_quality_status == "WARN"
    assert any("Snapshot quality preflight warning" in warning for warning in result.warnings)


def test_cli_current_candidates_works(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    calls = {}

    def fake_generate(*args, **kwargs):
        calls.update(kwargs)
        return _fake_current_result(tmp_path, status=None)

    monkeypatch.setattr("quant_replay_system.cli.generate_current_candidates", fake_generate)

    code = cli.main(
        [
            "current-candidates",
            "--date",
            "2024-03-01",
            "--universe",
            "unit_test",
            "--top",
            "2",
            "--output-dir",
            str(tmp_path / "current"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert calls["universe_name"] == "unit_test"
    assert calls["top_n"] == 2
    assert "candidate_count: 1" in output.out


def test_cli_prints_candidates_and_report_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.setattr(
        "quant_replay_system.cli.generate_current_candidates",
        lambda *args, **kwargs: _fake_current_result(tmp_path, status="PASS"),
    )

    code = cli.main(["current-candidates", "--date", "2024-03-01", "--universe", "unit_test"])
    output = capsys.readouterr()

    assert code == 0
    assert "candidates_path:" in output.out
    assert "report_path:" in output.out
    assert "Snapshot quality status: PASS" in output.out


def test_cli_snapshot_manifest_enables_preflight_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = tmp_path / "snapshot_manifest.json"
    manifest.write_text("{}", encoding="utf-8")

    def fake_generate(*args, **kwargs):
        assert Path(kwargs["snapshot_manifest_path"]) == manifest
        assert kwargs["config"].snapshot_quality_preflight.enabled is True
        return _fake_current_result(tmp_path, status="PASS")

    monkeypatch.setattr("quant_replay_system.cli.generate_current_candidates", fake_generate)

    code = cli.main(
        [
            "current-candidates",
            "--date",
            "2024-03-01",
            "--universe",
            "unit_test",
            "--snapshot-manifest",
            str(manifest),
        ]
    )

    assert code == 0


def test_cli_disable_snapshot_preflight_for_current_candidates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = tmp_path / "snapshot_manifest.json"
    manifest.write_text("{}", encoding="utf-8")

    def fake_generate(*args, **kwargs):
        assert kwargs["enable_snapshot_preflight"] is False
        assert kwargs["config"].snapshot_quality_preflight.enabled is False
        return _fake_current_result(tmp_path, status=None)

    monkeypatch.setattr("quant_replay_system.cli.generate_current_candidates", fake_generate)

    code = cli.main(
        [
            "current-candidates",
            "--date",
            "2024-03-01",
            "--universe",
            "unit_test",
            "--snapshot-manifest",
            str(manifest),
            "--disable-snapshot-preflight",
        ]
    )

    assert code == 0


def test_cli_prints_no_live_trading_statement(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.setattr(
        "quant_replay_system.cli.generate_current_candidates",
        lambda *args, **kwargs: _fake_current_result(tmp_path, status=None),
    )

    code = cli.main(["current-candidates", "--date", "2024-03-01", "--universe", "unit_test"])
    output = capsys.readouterr()

    assert code == 0
    assert "No live trading or broker API was invoked." in output.out


def test_cli_missing_required_input_produces_clear_error() -> None:
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["current-candidates", "--universe", "unit_test"])


def test_no_live_trading_or_broker_integration_is_invoked(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False


def test_no_network_or_api_calls_are_used(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert result.audit_metadata["current_candidate_generation_only"] is True


def test_current_candidate_run_id_is_deterministic() -> None:
    first = generate_current_candidate_run_id("2024-03-01", "unit_test", 2, "mvp", "snapshot.json")
    second = generate_current_candidate_run_id("2024-03-01", "unit_test", 2, "mvp", "snapshot.json")

    assert first == second


def _run(
    tmp_path: Path,
    *,
    top_n: int = 2,
    snapshot_manifest_path: Path | None = None,
) -> CurrentCandidateResult:
    return generate_current_candidates(
        DECISION_DATE,
        universe_name="unit_test",
        top_n=top_n,
        config=_settings(tmp_path),
        market_data=_make_market_data(["AAA", "BBB"]),
        universe_snapshot=_make_universe_snapshot(["AAA", "BBB"]),
        benchmark_data=_make_benchmark_data(),
        snapshot_manifest_path=snapshot_manifest_path,
        trading_calendar=_make_calendar(),
    )


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "current_candidates": settings.current_candidates.model_copy(
                update={
                    "output_dir": tmp_path / "current_candidates",
                    "min_action": "NO_TRADE",
                    "min_final_score": None,
                    "default_top_n": 2,
                    "write_artifacts": True,
                }
            ),
            "snapshot_quality_gate": settings.snapshot_quality_gate.model_copy(
                update={"output_dir": tmp_path / "snapshot_quality"}
            ),
            "paper_reconciliation": settings.paper_reconciliation.model_copy(
                update={"output_dir": tmp_path / "reconciliation"}
            ),
            "daily_paper_runner": settings.daily_paper_runner.model_copy(
                update={"output_dir": tmp_path / "paper_daily"}
            ),
        }
    )


def _make_calendar() -> TradingCalendar:
    dates = pd.date_range("2024-01-01", "2024-03-15", freq="D")
    rows = []
    for date in dates:
        is_weekend = date.weekday() >= 5
        is_holiday = date == pd.Timestamp("2024-03-06")
        is_trading = not is_weekend and not is_holiday
        rows.append(
            {
                "trade_date": date,
                "is_trading_day": is_trading,
                "session_open": "09:30" if is_trading else "",
                "session_close": "15:00" if is_trading else "",
                "decision_time": "15:30" if is_trading else "",
                "reason": "normal" if is_trading else ("holiday" if is_holiday else "weekend"),
            }
        )
    return TradingCalendar(pd.DataFrame(rows))


def _make_universe_snapshot(symbols: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "as_of_date": DECISION_DATE,
                "symbol": symbol,
                "name": f"{symbol} Fund",
                "instrument_type": "ETF",
                "exchange": "SSE",
                "listed_date": pd.Timestamp("2023-01-01"),
                "delisted_date": pd.NaT,
                "is_active": True,
                "is_st": False,
                "is_suspended": False,
                "industry": "Test",
                "min_lot": 100,
                "t_plus_rule": "t_plus_1",
                "available_time": pd.Timestamp("2024-03-01 09:00:00"),
                "revision_id": "u1",
                "source": "unit-test",
            }
            for symbol in symbols
        ]
    )


def _make_market_data(symbols: list[str]) -> pd.DataFrame:
    rows = []
    dates = pd.bdate_range("2024-01-01", "2024-03-15")
    dates = dates[dates != pd.Timestamp("2024-03-06")]
    for symbol_index, symbol in enumerate(symbols):
        offset = symbol_index * 20
        previous_close = None
        for idx, trade_date in enumerate(dates):
            close = 20 + offset + idx * (1.0 + symbol_index * 0.1)
            open_price = close - 0.25
            high = close + 0.8
            low = close - 0.8
            pre_close = previous_close if previous_close is not None else close - 1.0
            rows.append(
                {
                    "symbol": symbol,
                    "trade_date": trade_date,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": 1_000_000 + idx * 1_000 + symbol_index * 5_000,
                    "amount": 50_000_000 + idx * 500_000 + symbol_index * 1_000_000,
                    "pre_close": pre_close,
                    "adj_factor": 1.0,
                    "is_suspended": False,
                    "limit_up": close * 1.1,
                    "limit_down": close * 0.9,
                    "event_time": trade_date + pd.Timedelta(hours=15),
                    "publish_time": trade_date + pd.Timedelta(hours=15, minutes=5),
                    "ingest_time": trade_date + pd.Timedelta(hours=15, minutes=10),
                    "available_time": trade_date + pd.Timedelta(hours=15, minutes=10),
                    "revision_id": "m1",
                    "source": "unit-test",
                }
            )
            previous_close = close
    return pd.DataFrame(rows)


def _make_benchmark_data() -> pd.DataFrame:
    rows = []
    for idx, trade_date in enumerate(pd.bdate_range("2024-01-01", "2024-03-15")):
        if trade_date == pd.Timestamp("2024-03-06"):
            continue
        rows.append(
            {
                "symbol": "BENCH",
                "trade_date": trade_date,
                "close": 100 + idx * 0.5,
                "available_time": trade_date + pd.Timedelta(hours=15, minutes=10),
                "revision_id": "b1",
                "source": "unit-test",
            }
        )
    return pd.DataFrame(rows)


def _write_manifest(
    tmp_path: Path,
    *,
    bad_market: bool = False,
    bad_benchmark: bool = False,
    missing_listed_date: bool = False,
) -> Path:
    data_dir = tmp_path / "snapshot"
    data_dir.mkdir(parents=True, exist_ok=True)
    market = _make_market_data(["AAA", "BBB"]).copy()
    if bad_market:
        market.loc[0, "close"] = -1
    market_path = data_dir / "market.csv"
    market.to_csv(market_path, index=False)
    universe_path = data_dir / "universe.csv"
    universe = _make_universe_snapshot(["AAA", "BBB"])
    if missing_listed_date:
        universe["listed_date"] = pd.NaT
    universe.to_csv(universe_path, index=False)
    calendar_path = data_dir / "trading_calendar.csv"
    _make_calendar().frame.to_csv(calendar_path, index=False)
    benchmark_path = data_dir / "benchmark.csv"
    benchmark = _make_market_data(["BENCH"]).copy()
    if bad_benchmark:
        benchmark.loc[0, "high"] = 0.01
    benchmark.to_csv(benchmark_path, index=False)

    payload = {
        "snapshot_id": "current-candidate-test",
        "created_at": "2024-03-01T00:00:00",
        "market_path": str(market_path),
        "universe_path": str(universe_path),
        "trading_calendar_path": str(calendar_path),
        "benchmark_path": str(benchmark_path),
        "source": "unit-test",
        "revision_id": "v1",
    }
    manifest = tmp_path / "snapshot_manifest.json"
    manifest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return manifest


def _fake_current_result(tmp_path: Path, *, status: str | None) -> SimpleNamespace:
    report_path = tmp_path / "current_candidates_report.md"
    candidates_path = tmp_path / "candidates.csv"
    metadata = {
        "snapshot_quality_preflight_enabled": status is not None,
        "snapshot_quality_status": status,
        "snapshot_quality_report_path": tmp_path / "snapshot_quality_report.md" if status is not None else None,
        "snapshot_quality_gate_id": "gate123" if status is not None else None,
        "snapshot_quality_warnings": [],
    }
    return SimpleNamespace(
        run_id="current123",
        decision_date=DECISION_DATE,
        candidate_count=1,
        artifact_paths={
            "candidates": candidates_path,
            "current_candidates_report": report_path,
        },
        audit_metadata=metadata,
        warnings=[],
    )
