import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.advisory_profile_calibration import (
    evaluate_advisory_profile_thresholds,
    load_advisory_profile_calibration_input,
    run_advisory_profile_calibration,
)


def test_leading_zero_symbol_is_preserved(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, [_row(symbol="000001", final_score=82.0)])

    result = run_advisory_profile_calibration(
        fixture,
        input_type="candidates",
        profile="balanced",
        output_dir=tmp_path / "calibration",
    )
    output = pd.read_csv(result.artifact_paths["advisory_profile_calibration"], dtype={"symbol": str})

    assert result.calibration_frame.loc[0, "symbol"] == "000001"
    assert output.loc[0, "symbol"] == "000001"


def test_conservative_profile_labels_fewer_review_buy_candidates_than_experimental(tmp_path: Path) -> None:
    fixture = _write_fixture(
        tmp_path,
        [
            _row(symbol="000001", final_score=82.0),
            _row(symbol="510300", final_score=68.0),
            _row(symbol="600519", final_score=52.0),
        ],
    )

    conservative = run_advisory_profile_calibration(
        fixture,
        input_type="candidates",
        profile="conservative",
        output_dir=tmp_path / "conservative",
    )
    experimental = run_advisory_profile_calibration(
        fixture,
        input_type="candidates",
        profile="experimental",
        output_dir=tmp_path / "experimental",
    )

    assert conservative.label_counts["REVIEW_BUY_CANDIDATE"] == 1
    assert experimental.label_counts["REVIEW_BUY_CANDIDATE"] == 2
    assert conservative.label_counts["REVIEW_BUY_CANDIDATE"] < experimental.label_counts["REVIEW_BUY_CANDIDATE"]


def test_data_quality_fail_blocks_all_rows(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, [_row(symbol="000001", final_score=82.0), _row(symbol="510300", final_score=62.0)])

    result = run_advisory_profile_calibration(
        fixture,
        input_type="candidates",
        profile="balanced",
        data_quality_status="FAIL",
        snapshot_quality_status="PASS",
        output_dir=tmp_path / "calibration",
    )

    assert set(result.calibration_frame["simulated_advisory_label"]) == {"BLOCKED"}
    assert set(result.issues_frame["issue_code"]) == {"DATA_QUALITY_FAILED"}


def test_snapshot_quality_fail_blocks_all_rows(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, [_row(symbol="000001", final_score=82.0), _row(symbol="510300", final_score=62.0)])

    result = run_advisory_profile_calibration(
        fixture,
        input_type="candidates",
        profile="balanced",
        data_quality_status="PASS",
        snapshot_quality_status="FAIL",
        output_dir=tmp_path / "calibration",
    )

    assert set(result.calibration_frame["simulated_advisory_label"]) == {"BLOCKED"}
    assert set(result.issues_frame["issue_code"]) == {"SNAPSHOT_QUALITY_FAILED"}


def test_risk_blocked_row_becomes_blocked(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, [_row(risk_precheck_status="BLOCKED", risk_precheck_reason="manual risk block")])

    result = run_advisory_profile_calibration(
        fixture,
        input_type="candidates",
        profile="balanced",
        output_dir=tmp_path / "calibration",
    )

    assert result.calibration_frame.loc[0, "simulated_advisory_label"] == "BLOCKED"
    assert "RISK_BLOCKED" in result.issues_frame["issue_code"].tolist()


def test_missing_symbol_becomes_blocked_with_issue(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, [_row(symbol="")])

    result = run_advisory_profile_calibration(
        fixture,
        input_type="candidates",
        profile="balanced",
        output_dir=tmp_path / "calibration",
    )

    assert result.calibration_frame.loc[0, "simulated_advisory_label"] == "BLOCKED"
    assert "MISSING_SYMBOL" in result.issues_frame["issue_code"].tolist()


def test_demo_input_is_calibration_only_and_not_non_demo_review_label(tmp_path: Path) -> None:
    fixture = _write_fixture(
        tmp_path,
        [_row(symbol="000001", final_score=99.0, selection_profile="demo", demo_mode=True, not_strategy_recommendation=True)],
    )

    result = run_advisory_profile_calibration(
        fixture,
        input_type="candidates",
        profile="experimental",
        output_dir=tmp_path / "calibration",
    )

    row = result.calibration_frame.iloc[0]
    assert row["simulated_advisory_label"] == "DEMO_ONLY"
    assert bool(row["calibration_only"]) is True
    assert bool(row["not_trading_recommendation"]) is True


def test_manual_confirmation_and_safety_flags_are_always_set(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, [_row(symbol="000001", final_score=82.0)])

    result = run_advisory_profile_calibration(
        fixture,
        input_type="candidates",
        profile="balanced",
        output_dir=tmp_path / "calibration",
    )
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert result.calibration_frame["requires_manual_confirmation"].eq(True).all()
    assert result.calibration_frame["auto_order_allowed"].eq(False).all()
    assert result.calibration_frame["no_live_trading"].eq(True).all()
    assert result.calibration_frame["no_broker_api"].eq(True).all()
    assert result.calibration_frame["no_message_sent"].eq(True).all()
    assert metadata["requires_manual_confirmation"] is True
    assert metadata["auto_order_allowed"] is False
    assert metadata["no_live_trading"] is True
    assert metadata["no_broker_api"] is True
    assert metadata["no_message_sent"] is True
    assert metadata["message_sent"] is False
    assert metadata["broker_api_invoked"] is False
    assert metadata["live_trading_enabled"] is False


def test_load_and_evaluate_helpers_work_without_mutating_input(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path, [_row(symbol="000001", final_score=82.0), _row(symbol="510300", final_score=60.0)])
    loaded = load_advisory_profile_calibration_input(fixture, input_type="candidates")
    original = loaded.frame.copy(deep=True)

    result = evaluate_advisory_profile_thresholds(loaded, profile="balanced", output_dir=tmp_path / "calibration")

    pd.testing.assert_frame_equal(loaded.frame, original)
    assert result.row_count == 2
    assert result.label_counts["REVIEW_BUY_CANDIDATE"] == 1
    assert result.label_counts["WATCH"] == 1


def test_cli_advisory_profile_calibration_works(tmp_path: Path, capsys) -> None:
    fixture = _write_fixture(
        tmp_path,
        [_row(symbol="000001", final_score=82.0), _row(symbol="510300", final_score=60.0), _row(symbol="", final_score=75.0)],
    )

    code = cli.main(
        [
            "advisory-profile-calibration",
            "--input",
            str(fixture),
            "--input-type",
            "candidates",
            "--profile",
            "balanced",
            "--data-quality-status",
            "PASS",
            "--snapshot-quality-status",
            "PASS",
            "--output-dir",
            str(tmp_path / "calibration"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "calibration_run_id:" in output.out
    assert "profile: balanced" in output.out
    assert "REVIEW_BUY_CANDIDATE: 1" in output.out
    assert "WATCH: 1" in output.out
    assert "BLOCKED: 1" in output.out
    assert "No live trading, broker API, order placement, or message delivery was invoked." in output.out


def _write_fixture(tmp_path: Path, rows: list[dict[str, object]]) -> Path:
    path = tmp_path / "calibration_fixture.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _row(
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
        "name": "Local Fixture",
        "instrument_type": "STOCK",
        "final_score": final_score,
        "score_action": score_action,
        "action": action,
        "risk_precheck_status": risk_precheck_status,
        "risk_precheck_reason": risk_precheck_reason,
        "technical_score": 80.0,
        "liquidity_score": 70.0,
        "expectation_score": 60.0,
        "reality_score": 55.0,
        "sentiment_score": 50.0,
        "risk_penalty": 0.0,
        "score_breakdown": '{"final_score":72.0}',
        "selection_profile": selection_profile,
        "demo_mode": demo_mode,
        "not_strategy_recommendation": not_strategy_recommendation,
        "market_data_available": True,
        "execution_data_available": True,
        "snapshot_quality_status": "PASS",
        "data_quality_status": "PASS",
    }
