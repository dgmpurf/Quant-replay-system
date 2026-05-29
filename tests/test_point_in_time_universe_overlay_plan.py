import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.point_in_time_universe_overlay_plan import (
    build_point_in_time_universe_overlay_plan,
)


def test_pit_universe_overlay_plan_generates_manual_review_rows_for_universe_as_of_blockers(
    tmp_path: Path,
) -> None:
    manifest = _write_execution_manifest(tmp_path / "execution_manifest.csv")
    base_universe = _write_base_universe(tmp_path / "base_universe.csv")

    result = build_point_in_time_universe_overlay_plan(
        execution_manifest=manifest,
        base_universe=base_universe,
        universe_name="etf_core",
        output_dir=tmp_path / "out",
    )

    assert result.row_count == 2
    assert result.signal_date_count == 1
    assert result.symbol_count == 2
    assert result.review_status_counts == {"NEEDS_MANUAL_REVIEW": 2}
    assert result.survivorship_bias_warning_count == 2
    assert result.valid_for_signal_date_count == 0

    rows = result.plan_frame.sort_values("symbol").reset_index(drop=True)
    assert rows["signal_date"].tolist() == ["2024-04-02", "2024-04-02"]
    assert rows["symbol"].tolist() == ["000001", "510300"]
    assert rows["proposed_as_of_date"].tolist() == ["2024-04-02", "2024-04-02"]
    assert rows["proposed_available_time"].tolist() == ["2024-04-02 08:00:00", "2024-04-02 08:00:00"]
    assert rows["base_universe_as_of_date"].tolist() == ["2024-05-20", "2024-05-20"]
    assert rows["review_status"].eq("NEEDS_MANUAL_REVIEW").all()
    assert rows["manual_review_required"].eq(True).all()
    assert rows["survivorship_bias_warning"].eq(True).all()
    assert rows["valid_for_signal_date"].eq(False).all()
    assert rows["include_flag"].fillna("").eq("").all()
    assert rows["plan_only"].eq(True).all()
    assert rows["no_live_trading"].eq(True).all()
    assert rows["no_broker_api"].eq(True).all()
    assert rows["no_order_placement"].eq(True).all()
    assert rows["no_message_sent"].eq(True).all()

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["current_candidates_executed"] is False
    assert metadata["snapshot_manifest_built"] is False
    assert metadata["forward_returns_computed"] is False
    assert metadata["cache_mutated"] is False
    assert metadata["network_api_called"] is False
    assert metadata["llm_api_called"] is False


def test_pit_universe_overlay_plan_only_uses_blocked_universe_as_of_rows(tmp_path: Path) -> None:
    manifest = _write_execution_manifest(
        tmp_path / "execution_manifest.csv",
        include_ready_row=True,
    )
    base_universe = _write_base_universe(tmp_path / "base_universe.csv")

    result = build_point_in_time_universe_overlay_plan(
        execution_manifest=manifest,
        base_universe=base_universe,
        universe_name="etf_core",
        output_dir=tmp_path / "out",
    )

    assert result.signal_date_count == 1
    assert result.plan_frame["signal_date"].unique().tolist() == ["2024-04-02"]


def test_pit_universe_overlay_plan_can_leave_template_include_explicitly_enabled(
    tmp_path: Path,
) -> None:
    manifest = _write_execution_manifest(tmp_path / "execution_manifest.csv")
    base_universe = _write_base_universe(tmp_path / "base_universe.csv")

    result = build_point_in_time_universe_overlay_plan(
        execution_manifest=manifest,
        base_universe=base_universe,
        universe_name="etf_core",
        allow_template_include=True,
        output_dir=tmp_path / "out",
    )

    assert result.plan_frame["include_flag"].eq(True).all()
    assert result.plan_frame["review_status"].eq("NEEDS_MANUAL_REVIEW").all()
    assert result.plan_frame["valid_for_signal_date"].eq(False).all()


def test_pit_universe_overlay_plan_does_not_mutate_inputs_or_execute_workflows(tmp_path: Path) -> None:
    manifest = _write_execution_manifest(tmp_path / "execution_manifest.csv")
    base_universe = _write_base_universe(tmp_path / "base_universe.csv")
    manifest_before = manifest.read_text(encoding="utf-8")
    universe_before = base_universe.read_text(encoding="utf-8")

    result = build_point_in_time_universe_overlay_plan(
        execution_manifest=manifest,
        base_universe=base_universe,
        universe_name="etf_core",
        output_dir=tmp_path / "out",
    )

    assert manifest.read_text(encoding="utf-8") == manifest_before
    assert base_universe.read_text(encoding="utf-8") == universe_before
    assert result.audit_metadata["current_candidates_executed"] is False
    assert result.audit_metadata["snapshot_manifest_built"] is False
    assert result.audit_metadata["data_pipeline_executed"] is False
    assert result.audit_metadata["cache_mutated"] is False
    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["message_sent"] is False


def test_cli_pit_universe_overlay_plan_works(tmp_path: Path, capsys) -> None:
    manifest = _write_execution_manifest(tmp_path / "execution_manifest.csv")
    base_universe = _write_base_universe(tmp_path / "base_universe.csv")

    code = cli.main(
        [
            "pit-universe-overlay-plan",
            "--execution-manifest",
            str(manifest),
            "--base-universe",
            str(base_universe),
            "--universe-name",
            "etf_core",
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    output = capsys.readouterr()
    assert code == 0
    assert "overlay_plan_id:" in output.out
    assert "row_count: 2" in output.out
    assert "signal_date_count: 1" in output.out
    assert "symbol_count: 2" in output.out
    assert "NEEDS_MANUAL_REVIEW=2" in output.out
    assert "survivorship_bias_warning_count: 2" in output.out
    assert "valid_for_signal_date_count: 0" in output.out
    assert "No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM API, or external API was invoked." in output.out


def _write_execution_manifest(
    path: Path,
    *,
    include_ready_row: bool = False,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "execution_manifest_id": "exec001",
            "plan_id": "plan001",
            "signal_date": "2024-04-02",
            "universe": "etf_core",
            "selection_profile": "demo",
            "plan_status": "READY",
            "warmup_available": True,
            "candidate_generation_feasible": True,
            "forward_1d_available": True,
            "forward_3d_available": True,
            "forward_5d_available": True,
            "forward_10d_available": True,
            "required_snapshot_manifest_path": "snapshot_manifest.json",
            "snapshot_manifest_found": True,
            "snapshot_quality_status": "PASS",
            "market_dataset_path": "",
            "universe_dataset_path": "base_universe.csv",
            "universe_as_of_date": "2024-05-20",
            "universe_valid_for_signal_date": False,
            "trading_calendar_path": "",
            "source_policy": "reviewed_local_v0",
            "recommended_source_filter": "AKSHARE_OPTIONAL",
            "recommended_upstream_filter": "TENCENT_FOR_STOCKS;SINA_FOR_ETFS",
            "readiness_status": "BLOCKED_UNIVERSE_AS_OF",
            "blocker_reason": "Universe as_of_date is later than signal date.",
            "reviewed_execution_required": True,
            "no_live_trading": True,
            "no_broker_api": True,
            "no_order_placement": True,
            "no_message_sent": True,
            "plan_only": True,
        }
    ]
    if include_ready_row:
        ready = dict(rows[0])
        ready.update(
            {
                "signal_date": "2024-04-09",
                "universe_as_of_date": "2024-04-08",
                "universe_valid_for_signal_date": True,
                "readiness_status": "READY_FOR_REVIEW",
                "blocker_reason": "",
            }
        )
        rows.append(ready)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _write_base_universe(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            _universe_row("000001", "Ping An Bank", "STOCK"),
            _universe_row("510300", "CSI 300 ETF", "ETF"),
        ]
    ).to_csv(path, index=False)
    return path


def _universe_row(symbol: str, name: str, instrument_type: str) -> dict:
    return {
        "as_of_date": "2024-05-20",
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
        "available_time": "2024-05-20 08:00:00",
        "revision_id": "v1",
        "source": "LOCAL_TEST",
        "upstream_source": "LOCAL_TEST",
    }
