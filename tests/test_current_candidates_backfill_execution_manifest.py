import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.current_candidates_backfill_execution_manifest import (
    build_current_candidates_backfill_execution_manifest,
)


def test_execution_manifest_reads_plan_and_blocks_missing_snapshot(tmp_path: Path) -> None:
    plan = _write_plan(tmp_path / "plan.csv")

    result = build_current_candidates_backfill_execution_manifest(
        plan=plan,
        snapshot_root=tmp_path / "snapshots",
        snapshot_quality_root=tmp_path / "snapshot_quality",
        universe_root=tmp_path / "universe_root",
        output_dir=tmp_path / "out",
    )

    assert result.row_count == 1
    row = result.manifest_frame.iloc[0]
    assert row["plan_id"] == "plan001"
    assert row["signal_date"] == "2024-04-02"
    assert row["readiness_status"] == "BLOCKED_MISSING_SNAPSHOT"
    assert row["snapshot_manifest_found"] is False
    assert row["reviewed_execution_required"] is True
    assert row["no_live_trading"] is True
    assert row["no_broker_api"] is True
    assert row["no_order_placement"] is True
    assert row["no_message_sent"] is True
    assert row["plan_only"] is True
    assert result.audit_metadata["current_candidates_executed"] is False
    assert result.audit_metadata["snapshot_manifest_built"] is False
    assert result.audit_metadata["cache_mutated"] is False


def test_execution_manifest_blocks_universe_as_of_after_signal_date(tmp_path: Path) -> None:
    plan = _write_plan(tmp_path / "plan.csv", signal_date="2024-04-02")
    _write_snapshot(
        tmp_path,
        snapshot_id="snapshot_late_universe",
        universe_as_of_date="2024-05-20",
        universe_available_time="2024-05-20 08:00:00",
        snapshot_quality_status="PASS",
    )

    result = build_current_candidates_backfill_execution_manifest(
        plan=plan,
        snapshot_root=tmp_path / "data_pipeline",
        snapshot_quality_root=tmp_path / "snapshot_quality",
        output_dir=tmp_path / "out",
    )

    row = result.manifest_frame.iloc[0]
    assert row["readiness_status"] == "BLOCKED_UNIVERSE_AS_OF"
    assert row["snapshot_manifest_found"] is True
    assert row["snapshot_quality_status"] == "PASS"
    assert row["universe_as_of_date"].startswith("2024-05-20")
    assert row["universe_valid_for_signal_date"] is False
    assert "later than signal date" in row["blocker_reason"]


def test_execution_manifest_marks_valid_snapshot_ready_for_review(tmp_path: Path) -> None:
    plan = _write_plan(tmp_path / "plan.csv", signal_date="2024-04-02")
    snapshot_manifest = _write_snapshot(
        tmp_path,
        snapshot_id="snapshot_valid",
        universe_as_of_date="2024-04-01",
        universe_available_time="2024-04-01 08:00:00",
        snapshot_quality_status="PASS",
    )

    result = build_current_candidates_backfill_execution_manifest(
        plan=plan,
        snapshot_root=tmp_path / "data_pipeline",
        snapshot_quality_root=tmp_path / "snapshot_quality",
        output_dir=tmp_path / "out",
    )

    row = result.manifest_frame.iloc[0]
    assert row["readiness_status"] == "READY_FOR_REVIEW"
    assert row["required_snapshot_manifest_path"] == str(snapshot_manifest)
    assert row["snapshot_manifest_found"] is True
    assert row["snapshot_quality_status"] == "PASS"
    assert row["universe_valid_for_signal_date"] is True
    assert result.ready_count == 1
    assert result.blocked_count == 0


def test_execution_manifest_blocks_plan_infeasible_before_snapshot_checks(tmp_path: Path) -> None:
    plan = _write_plan(
        tmp_path / "plan.csv",
        row_updates={"warmup_available": False, "candidate_generation_feasible": False},
    )
    _write_snapshot(
        tmp_path,
        snapshot_id="snapshot_valid",
        universe_as_of_date="2024-04-01",
        universe_available_time="2024-04-01 08:00:00",
        snapshot_quality_status="PASS",
    )

    result = build_current_candidates_backfill_execution_manifest(
        plan=plan,
        snapshot_root=tmp_path / "data_pipeline",
        snapshot_quality_root=tmp_path / "snapshot_quality",
        output_dir=tmp_path / "out",
    )

    row = result.manifest_frame.iloc[0]
    assert row["readiness_status"] == "BLOCKED_PLAN_INFEASIBLE"
    assert "warmup_available=false" in row["blocker_reason"]


def test_execution_manifest_cli_writes_artifacts(tmp_path: Path, capsys) -> None:
    plan = _write_plan(tmp_path / "plan.csv")

    code = cli.main(
        [
            "current-candidates-backfill-execution-manifest",
            "--plan",
            str(plan),
            "--snapshot-root",
            str(tmp_path / "snapshots"),
            "--snapshot-quality-root",
            str(tmp_path / "snapshot_quality"),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    output = capsys.readouterr()
    assert code == 0
    assert "execution_manifest_id:" in output.out
    assert "row_count: 1" in output.out
    assert "BLOCKED_MISSING_SNAPSHOT=1" in output.out
    assert "No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, or network/API call was invoked." in output.out


def test_execution_manifest_does_not_mutate_inputs_or_enable_execution(tmp_path: Path) -> None:
    plan = _write_plan(tmp_path / "plan.csv")
    before = plan.read_text(encoding="utf-8")

    result = build_current_candidates_backfill_execution_manifest(
        plan=plan,
        snapshot_root=tmp_path / "snapshots",
        snapshot_quality_root=tmp_path / "snapshot_quality",
        output_dir=tmp_path / "out",
    )

    assert plan.read_text(encoding="utf-8") == before
    assert result.audit_metadata["current_candidates_executed"] is False
    assert result.audit_metadata["data_pipeline_executed"] is False
    assert result.audit_metadata["snapshot_manifest_built"] is False
    assert result.audit_metadata["forward_returns_computed"] is False
    assert result.audit_metadata["cache_mutated"] is False
    assert result.audit_metadata["network_api_called"] is False
    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["message_sent"] is False


def _write_plan(path: Path, *, signal_date: str = "2024-04-02", row_updates: dict | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "plan_id": "plan001",
        "signal_date": signal_date,
        "universe": "etf_core",
        "selection_profile": "demo",
        "eligible_symbol_count": 2,
        "total_symbol_count": 2,
        "min_required_symbol_count": 2,
        "max_forward_horizon": 10,
        "warmup_trading_days": 60,
        "warmup_available": True,
        "earliest_required_warmup_date": "2024-01-02",
        "first_available_market_date": "2024-01-02",
        "warmup_start_date": "2024-01-02",
        "warmup_reason": "Warmup window has 60 trading-day coverage through signal date.",
        "forward_1d_available": True,
        "forward_3d_available": True,
        "forward_5d_available": True,
        "forward_10d_available": True,
        "latest_required_forward_date": "2024-04-18",
        "cache_start_date": "2024-01-02",
        "cache_end_date": "2024-05-20",
        "source_policy": "reviewed_local_v0",
        "recommended_source_filter": "AKSHARE_OPTIONAL",
        "recommended_upstream_filter": "TENCENT_FOR_STOCKS;SINA_FOR_ETFS",
        "status": "READY",
        "reason": "Plan row has required warmup, forward horizons, and symbol coverage.",
        "candidate_generation_feasible": True,
        "candidate_generation_blocker": "",
        "symbols": "000001;510300",
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
    }
    row.update(row_updates or {})
    pd.DataFrame([row]).to_csv(path, index=False)
    return path


def _write_snapshot(
    root: Path,
    *,
    snapshot_id: str,
    universe_as_of_date: str,
    universe_available_time: str,
    snapshot_quality_status: str,
) -> Path:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    market_path = data_dir / f"{snapshot_id}_market.csv"
    universe_path = data_dir / f"{snapshot_id}_universe.csv"
    calendar_path = data_dir / f"{snapshot_id}_calendar.csv"
    manifest_dir = root / "data_pipeline" / snapshot_id
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / "snapshot_manifest.json"

    pd.DataFrame(
        [
            _market_row("000001", "2024-04-02"),
            _market_row("510300", "2024-04-02"),
        ]
    ).to_csv(market_path, index=False)
    pd.DataFrame(
        [
            _universe_row("000001", "Ping An Bank", "STOCK", universe_as_of_date, universe_available_time),
            _universe_row("510300", "CSI 300 ETF", "ETF", universe_as_of_date, universe_available_time),
        ]
    ).to_csv(universe_path, index=False)
    pd.DataFrame(
        [
            {
                "trade_date": "2024-04-02",
                "is_trading_day": True,
                "session_open": "09:30:00",
                "session_close": "15:00:00",
                "decision_time": "2024-04-02 15:30:00",
                "reason": "",
            }
        ]
    ).to_csv(calendar_path, index=False)
    manifest_path.write_text(
        json.dumps(
            {
                "snapshot_id": snapshot_id,
                "processed_files": {
                    "market": str(market_path),
                    "universe": str(universe_path),
                    "trading_calendar": str(calendar_path),
                },
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    quality_dir = root / "snapshot_quality" / f"{snapshot_id}_quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    (quality_dir / "metadata.json").write_text(
        json.dumps(
            {
                "snapshot_id": snapshot_id,
                "status": snapshot_quality_status,
                "artifact_paths": {"snapshot_quality_gate_report": str(quality_dir / "report.md")},
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (quality_dir / "report.md").write_text("snapshot quality", encoding="utf-8")
    return manifest_path


def _market_row(symbol: str, trade_date: str) -> dict:
    return {
        "symbol": symbol,
        "trade_date": trade_date,
        "open": 10,
        "high": 11,
        "low": 9,
        "close": 10.5,
        "volume": 1000,
        "amount": 10000,
        "pre_close": 10,
        "adj_factor": 1,
        "is_suspended": False,
        "limit_up": 11,
        "limit_down": 9,
        "event_time": f"{trade_date} 15:00:00",
        "publish_time": f"{trade_date} 15:10:00",
        "ingest_time": f"{trade_date} 15:20:00",
        "available_time": f"{trade_date} 15:30:00",
        "revision_id": "v1",
        "source": "AKSHARE_OPTIONAL",
    }


def _universe_row(
    symbol: str,
    name: str,
    instrument_type: str,
    as_of_date: str,
    available_time: str,
) -> dict:
    return {
        "as_of_date": as_of_date,
        "symbol": symbol,
        "name": name,
        "instrument_type": instrument_type,
        "exchange": "CN",
        "listed_date": "",
        "delisted_date": "",
        "is_active": True,
        "is_st": False,
        "is_suspended": False,
        "industry": "",
        "min_lot": 100,
        "t_plus_rule": "T+1",
        "available_time": available_time,
        "revision_id": "v1",
        "source": "LOCAL_TEST",
    }
