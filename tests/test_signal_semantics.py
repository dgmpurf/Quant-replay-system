import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.signal_semantics import (
    SIGNAL_SEMANTICS_COLUMNS,
    classify_signal_semantics_action,
    run_signal_semantics,
)


def test_demo_candidate_rows_become_demo_only_not_review_buy(tmp_path: Path) -> None:
    input_path, metadata_path = _write_demo_candidates(tmp_path)

    result = run_signal_semantics(
        input_path,
        input_type="candidates",
        metadata_path=metadata_path,
        profile="demo",
        settings=_settings(tmp_path),
    )

    assert result.row_count == 2
    assert result.action_counts["DEMO_ONLY"] == 2
    assert result.action_counts["REVIEW_BUY_CANDIDATE"] == 0
    assert result.decisions["not_strategy_recommendation"].map(bool).all()
    assert set(SIGNAL_SEMANTICS_COLUMNS).issubset(result.decisions.columns)


def test_high_score_demo_still_remains_demo_only() -> None:
    row = _base_row(
        final_score=99.0,
        score_action="PAPER_TRADE",
        action="PAPER_TRADE",
        selection_profile="demo",
        demo_mode=True,
        not_strategy_recommendation=True,
    )

    assert classify_signal_semantics_action(row) == "DEMO_ONLY"


def test_non_demo_high_score_can_be_review_buy_candidate_but_never_auto_order(tmp_path: Path) -> None:
    fixture = _write_fixture(
        tmp_path,
        [
            _base_row(
                symbol="000001",
                final_score=88.0,
                score_action="PAPER_TRADE",
                action="PAPER_TRADE",
                selection_profile="reviewed_local_v0",
                demo_mode=False,
                not_strategy_recommendation=False,
            )
        ],
    )

    result = run_signal_semantics(
        fixture,
        input_type="candidates",
        profile="reviewed_local_v0",
        settings=_settings(tmp_path),
    )

    record = result.decisions.iloc[0].to_dict()
    assert record["advisory_action"] == "REVIEW_BUY_CANDIDATE"
    assert record["requires_manual_confirmation"] is True
    assert record["auto_order_allowed"] is False
    assert record["no_live_trading"] is True
    assert record["no_broker_api"] is True


def test_blocked_risk_row_becomes_blocked(tmp_path: Path) -> None:
    fixture = _write_fixture(
        tmp_path,
        [_base_row(risk_precheck_status="BLOCKED", risk_precheck_reason="manual risk block")],
    )

    result = run_signal_semantics(fixture, input_type="candidates", settings=_settings(tmp_path))

    assert result.decisions.loc[0, "advisory_action"] == "BLOCKED"
    assert "RISK_BLOCKED" in result.issues["issue_code"].tolist()


def test_missing_symbol_becomes_blocked_with_issue(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, [_base_row(symbol="")])

    result = run_signal_semantics(fixture, input_type="candidates", settings=_settings(tmp_path))

    assert result.decisions.loc[0, "advisory_action"] == "BLOCKED"
    assert "MISSING_SYMBOL" in result.issues["issue_code"].tolist()


def test_data_quality_fail_blocks(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, [_base_row(final_score=90.0, score_action="PAPER_TRADE")])

    result = run_signal_semantics(
        fixture,
        input_type="candidates",
        data_quality_status="FAIL",
        profile="reviewed_local_v0",
        settings=_settings(tmp_path),
    )

    assert result.decisions.loc[0, "advisory_action"] == "BLOCKED"
    assert "DATA_QUALITY_FAILED" in result.issues["issue_code"].tolist()


def test_snapshot_quality_fail_blocks(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, [_base_row(final_score=90.0, score_action="PAPER_TRADE")])

    result = run_signal_semantics(
        fixture,
        input_type="candidates",
        snapshot_quality_status="FAIL",
        profile="reviewed_local_v0",
        settings=_settings(tmp_path),
    )

    assert result.decisions.loc[0, "advisory_action"] == "BLOCKED"
    assert "SNAPSHOT_QUALITY_FAILED" in result.issues["issue_code"].tolist()


def test_no_trade_non_demo_row_becomes_no_action(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, [_base_row(score_action="NO_TRADE", action="NO_TRADE", final_score=82.0)])

    result = run_signal_semantics(
        fixture,
        input_type="candidates",
        profile="reviewed_local_v0",
        settings=_settings(tmp_path),
    )

    assert result.decisions.loc[0, "advisory_action"] == "NO_ACTION"


def test_leading_zero_symbol_is_preserved(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, [_base_row(symbol="000001")])

    result = run_signal_semantics(fixture, input_type="candidates", settings=_settings(tmp_path))
    output = pd.read_csv(result.artifact_paths["signal_semantics"], dtype={"symbol": str})

    assert result.decisions.loc[0, "symbol"] == "000001"
    assert output.loc[0, "symbol"] == "000001"


def test_cli_signal_semantics_works(tmp_path: Path, capsys) -> None:
    input_path, metadata_path = _write_demo_candidates(tmp_path)

    code = cli.main(
        [
            "signal-semantics",
            "--input",
            str(input_path),
            "--input-type",
            "candidates",
            "--metadata",
            str(metadata_path),
            "--profile",
            "demo",
            "--output-dir",
            str(tmp_path / "signal_semantics"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "semantics_run_id:" in output.out
    assert "row_count: 2" in output.out
    assert "DEMO_ONLY: 2" in output.out
    assert "review_buy_candidate_count: 0" in output.out
    assert "No alert message was sent." in output.out


def test_no_live_trading_broker_network_message_or_approved_for_paper(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, [_base_row(symbol="000001")])

    result = run_signal_semantics(fixture, input_type="candidates", settings=_settings(tmp_path))
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["no_live_trading"] is True
    assert metadata["no_broker_api"] is True
    assert metadata["no_message_sent"] is True
    assert metadata["message_sent"] is False
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False
    assert metadata["approved_for_paper_applied"] is False
    assert metadata["auto_order_allowed"] is False


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "signal_semantics": settings.signal_semantics.model_copy(
                update={"output_dir": tmp_path / "signal_semantics", "write_artifacts": True}
            )
        }
    )


def _write_demo_candidates(tmp_path: Path) -> tuple[Path, Path]:
    artifact_dir = tmp_path / "current_candidates" / "demo"
    artifact_dir.mkdir(parents=True)
    rows = [
        _base_row(
            symbol="000001",
            final_score=99.0,
            score_action="PAPER_TRADE",
            action="PAPER_TRADE",
            selection_profile="demo",
            demo_mode=True,
            not_strategy_recommendation=True,
        ),
        _base_row(
            symbol="510300",
            final_score=55.0,
            score_action="NO_TRADE",
            action="NO_TRADE",
            selection_profile="demo",
            demo_mode=True,
            not_strategy_recommendation=True,
        ),
    ]
    candidates_path = artifact_dir / "candidates.csv"
    pd.DataFrame(rows).to_csv(candidates_path, index=False)
    metadata = {
        "run_id": "demo123",
        "selection_profile": "demo",
        "demo_mode": True,
        "not_strategy_recommendation": True,
    }
    metadata_path = artifact_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    return candidates_path, metadata_path


def _write_fixture(tmp_path: Path, rows: list[dict[str, object]]) -> Path:
    path = tmp_path / "fixture.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _base_row(
    *,
    symbol: str = "000001",
    final_score: float = 72.0,
    score_action: str = "PAPER_TRADE",
    action: str = "PAPER_TRADE",
    risk_precheck_status: str = "PASS",
    risk_precheck_reason: str = "eligible",
    selection_profile: str = "reviewed_local_v0",
    demo_mode: bool = False,
    not_strategy_recommendation: bool = False,
) -> dict[str, object]:
    return {
        "symbol": symbol,
        "name": "Ping An Bank",
        "instrument_type": "STOCK",
        "final_score": final_score,
        "score_action": score_action,
        "action": action,
        "risk_precheck_status": risk_precheck_status,
        "risk_precheck_reason": risk_precheck_reason,
        "technical_score": 80.0,
        "liquidity_score": 70.0,
        "expectation_score": 65.0,
        "reality_score": 60.0,
        "sentiment_score": 55.0,
        "score_reason": "synthetic local fixture",
        "score_breakdown": '{"final_score":72.0}',
        "selection_profile": selection_profile,
        "demo_mode": demo_mode,
        "not_strategy_recommendation": not_strategy_recommendation,
        "snapshot_quality_status": "PASS",
        "data_quality_status": "PASS",
    }
