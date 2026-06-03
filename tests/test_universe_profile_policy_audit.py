from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system import cli
from quant_replay_system.universe_profile_policy_audit import (
    UniverseProfilePolicyAuditSettings,
    build_universe_profile_policy_audit,
)


def test_mixed_etf_core_is_classified_as_legacy_mixed_demo_universe(tmp_path: Path) -> None:
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [
            _worklist_row("2024-04-02", "000001", "etf_core", "STOCK"),
            _worklist_row("2024-04-02", "510300", "etf_core", "ETF"),
        ],
    )

    result = build_universe_profile_policy_audit(worklist=worklist, output_dir=tmp_path / "out")

    assert result.row_count == 2
    assert result.mixed_universe_count == 1
    assert result.ambiguous_policy_count == 2
    assert set(result.audit_frame["profile_policy_classification"]) == {"legacy_mixed_demo_universe"}
    assert set(result.audit_frame["policy_issue"]) == {"POLICY_AMBIGUOUS_DEMO_MIXED_UNIVERSE"}
    assert set(result.audit_frame["legacy_universe_classification"]) == {"legacy_mixed_demo_universe"}


def test_etf_core_with_mixed_instruments_is_not_treated_as_etf_only(tmp_path: Path) -> None:
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [
            _worklist_row("2024-04-02", "000001", "etf_core", "STOCK"),
            _worklist_row("2024-04-02", "159915", "etf_core", "ETF"),
        ],
    )

    result = build_universe_profile_policy_audit(worklist=worklist, output_dir=tmp_path / "out")

    assert "etf_only_universe" not in set(result.audit_frame["profile_policy_classification"])
    assert result.status == "WARN"


def test_stock_and_etf_rows_recommend_split_profiles(tmp_path: Path) -> None:
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [
            _worklist_row("2024-04-02", "000001", "etf_core", "STOCK"),
            _worklist_row("2024-04-02", "510300", "etf_core", "ETF"),
        ],
    )

    result = build_universe_profile_policy_audit(worklist=worklist, output_dir=tmp_path / "out")

    recommendations = dict(zip(result.audit_frame["symbol"], result.audit_frame["recommended_future_universe"]))
    assert recommendations["000001"] == "stock_core"
    assert recommendations["510300"] == "etf_core"
    assert result.recommended_stock_core_count == 1
    assert result.recommended_etf_core_count == 1


def test_mixed_demo_core_preserves_mixed_demo_guidance(tmp_path: Path) -> None:
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [
            _worklist_row("2024-04-02", "000001", "mixed_demo_core", "STOCK"),
            _worklist_row("2024-04-02", "510300", "mixed_demo_core", "ETF"),
            _worklist_row("2024-04-02", "999999", "mixed_demo_core", ""),
        ],
    )

    result = build_universe_profile_policy_audit(worklist=worklist, output_dir=tmp_path / "out")

    assert set(result.audit_frame["profile_policy_classification"]) == {"mixed_demo_universe"}
    unknown_row = result.audit_frame[result.audit_frame["symbol"] == "999999"].iloc[0]
    assert unknown_row["recommended_future_universe"] == "mixed_demo_core"


def test_leading_zero_symbols_are_preserved_and_no_review_decision_is_applied(tmp_path: Path) -> None:
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [
            _worklist_row("2024-04-02", "000001", "stock_core", "STOCK"),
        ],
    )

    result = build_universe_profile_policy_audit(worklist=worklist, output_dir=tmp_path / "out")

    row = result.audit_frame.iloc[0]
    assert row["symbol"] == "000001"
    assert row["should_approve"] == False  # noqa: E712
    assert row["should_reject"] == False  # noqa: E712
    assert row["no_universe_export"] == True  # noqa: E712
    assert row["no_data_raw_write"] == True  # noqa: E712
    assert row["no_data_processed_write"] == True  # noqa: E712
    assert row["no_current_candidates_generated"] == True  # noqa: E712
    assert row["no_snapshot_built"] == True  # noqa: E712
    assert row["no_forward_labels"] == True  # noqa: E712
    assert row["no_live_trading"] == True  # noqa: E712
    assert row["no_broker_api"] == True  # noqa: E712
    assert row["no_order_placement"] == True  # noqa: E712
    assert row["no_message_sent"] == True  # noqa: E712
    assert row["audit_only"] == True  # noqa: E712


def test_worklist_and_review_inputs_are_deduped_by_signal_symbol_universe(tmp_path: Path) -> None:
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [
            _worklist_row("2024-04-02", "000001", "etf_core", "STOCK"),
            _worklist_row("2024-04-02", "510300", "etf_core", "ETF"),
        ],
    )
    review = _write_review(
        tmp_path / "review.csv",
        [
            _review_row("2024-04-02", "000001", "etf_core", "STOCK"),
            _review_row("2024-04-02", "510300", "etf_core", "ETF"),
        ],
    )

    result = build_universe_profile_policy_audit(worklist=worklist, review=review, output_dir=tmp_path / "out")

    assert result.row_count == 2
    assert result.stock_row_count == 1
    assert result.etf_row_count == 1


def test_at_least_one_artifact_source_is_required(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="At least one"):
        build_universe_profile_policy_audit(output_dir=tmp_path / "out")


def test_unsafe_settings_are_rejected(tmp_path: Path) -> None:
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [_worklist_row("2024-04-02", "000001", "stock_core", "STOCK")],
    )

    with pytest.raises(ValueError, match="report-only"):
        build_universe_profile_policy_audit(
            worklist=worklist,
            output_dir=tmp_path / "out",
            settings=UniverseProfilePolicyAuditSettings(enable_universe_export=True),
        )


def test_cli_universe_profile_policy_audit_works(tmp_path: Path, capsys) -> None:
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [
            _worklist_row("2024-04-02", "000001", "etf_core", "STOCK"),
            _worklist_row("2024-04-02", "159915", "etf_core", "ETF"),
        ],
    )

    code = cli.main(
        [
            "universe-profile-policy-audit",
            "--worklist",
            str(worklist),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    output = capsys.readouterr()
    assert code == 0
    assert "audit_id:" in output.out
    assert "row_count: 2" in output.out
    assert "stock_row_count: 1" in output.out
    assert "etf_row_count: 1" in output.out
    assert "ambiguous_policy_count: 2" in output.out
    assert "No approval, rejection, universe export" in output.out


def _write_worklist(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _write_review(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _worklist_row(signal_date: str, symbol: str, universe_name: str, suggested_instrument_type: str) -> dict:
    return {
        "worklist_id": "worklist001",
        "review_id": "review001",
        "signal_date": signal_date,
        "symbol": symbol,
        "universe_name": universe_name,
        "suggested_instrument_type": suggested_instrument_type,
        "current_review_status": "NEEDS_MANUAL_REVIEW",
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "worklist_only": True,
    }


def _review_row(signal_date: str, symbol: str, universe_name: str, instrument_type: str) -> dict:
    return {
        "review_id": "review001",
        "signal_date": signal_date,
        "symbol": symbol,
        "universe_name": universe_name,
        "instrument_type": instrument_type,
        "review_status": "NEEDS_MANUAL_REVIEW",
        "valid_for_signal_date": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "review_only": True,
    }
