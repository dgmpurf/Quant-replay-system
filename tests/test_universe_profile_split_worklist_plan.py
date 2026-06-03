from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system import cli
from quant_replay_system.universe_profile_policy_audit import build_universe_profile_policy_audit
from quant_replay_system.universe_profile_split_worklist_plan import (
    UniverseProfileSplitWorklistPlanSettings,
    build_universe_profile_split_worklist_plan,
    load_universe_profile_registry,
)


def test_registry_loads_initial_profiles(tmp_path: Path) -> None:
    registry_path = _write_registry(tmp_path / "profiles.yaml")

    registry = load_universe_profile_registry(registry_path)

    assert set(registry) == {"stock_core", "etf_core", "mixed_demo_core"}
    assert registry["stock_core"].allowed_instrument_types == ("STOCK",)
    assert registry["etf_core"].allowed_instrument_types == ("ETF",)
    assert registry["mixed_demo_core"].allowed_instrument_types == ("STOCK", "ETF")
    assert registry["mixed_demo_core"].mixed_allowed is True
    assert registry["mixed_demo_core"].demo_only is True


def test_stock_and_etf_rows_map_to_split_profiles(tmp_path: Path) -> None:
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [
            _worklist_row("2024-04-02", "000001", "etf_core", "STOCK"),
            _worklist_row("2024-04-02", "510300", "etf_core", "ETF"),
        ],
    )
    registry_path = _write_registry(tmp_path / "profiles.yaml")
    policy = build_universe_profile_policy_audit(worklist=worklist, output_dir=tmp_path / "audit")

    result = build_universe_profile_split_worklist_plan(
        worklist=worklist,
        policy_audit=policy.artifact_paths["audit_csv"],
        profiles=registry_path,
        output_dir=tmp_path / "plan",
    )

    recommendations = dict(zip(result.plan_frame["symbol"], result.plan_frame["recommended_future_universe"]))
    assert recommendations["000001"] == "stock_core"
    assert recommendations["510300"] == "etf_core"
    assert result.stock_row_count == 1
    assert result.etf_row_count == 1
    assert result.recommended_stock_core_count == 1
    assert result.recommended_etf_core_count == 1


def test_mixed_legacy_etf_core_rows_are_classified_as_legacy_context(tmp_path: Path) -> None:
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [
            _worklist_row("2024-04-02", "000001", "etf_core", "STOCK"),
            _worklist_row("2024-04-02", "510300", "etf_core", "ETF"),
        ],
    )
    registry_path = _write_registry(tmp_path / "profiles.yaml")
    policy = build_universe_profile_policy_audit(worklist=worklist, output_dir=tmp_path / "audit")

    result = build_universe_profile_split_worklist_plan(
        policy_audit=policy.artifact_paths["audit_csv"],
        profiles=registry_path,
        output_dir=tmp_path / "plan",
    )

    assert result.legacy_mixed_demo_row_count == 2
    assert set(result.plan_frame["legacy_classification"]) == {"legacy_mixed_demo_universe"}
    assert set(result.plan_frame["profile_rule_applied"]) == {"LEGACY_ETF_CORE_SPLIT_BY_INSTRUMENT_TYPE"}


def test_current_active_worklist_is_not_mutated_and_leading_zero_symbol_is_preserved(tmp_path: Path) -> None:
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [_worklist_row("2024-04-02", "000001", "etf_core", "STOCK")],
    )
    before = worklist.read_text(encoding="utf-8")
    registry_path = _write_registry(tmp_path / "profiles.yaml")

    result = build_universe_profile_split_worklist_plan(
        worklist=worklist,
        profiles=registry_path,
        output_dir=tmp_path / "plan",
    )

    assert worklist.read_text(encoding="utf-8") == before
    row = result.plan_frame.iloc[0]
    assert row["symbol"] == "000001"
    assert row["should_mutate_active_worklist"] == False  # noqa: E712
    assert row["should_approve"] == False  # noqa: E712
    assert row["should_reject"] == False  # noqa: E712


def test_profile_conflict_is_reported_for_stock_under_future_etf_core(tmp_path: Path) -> None:
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [_worklist_row("2024-04-02", "000001", "etf_core", "STOCK")],
    )
    registry_path = _write_registry(tmp_path / "profiles.yaml")

    result = build_universe_profile_split_worklist_plan(
        worklist=worklist,
        profiles=registry_path,
        output_dir=tmp_path / "plan",
    )

    row = result.plan_frame.iloc[0]
    assert row["profile_conflict"] == True  # noqa: E712
    assert "STOCK is not allowed" in row["conflict_reason"]
    assert result.profile_conflict_count == 1


def test_safety_flags_block_unsafe_settings(tmp_path: Path) -> None:
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [_worklist_row("2024-04-02", "000001", "stock_core", "STOCK")],
    )
    registry_path = _write_registry(tmp_path / "profiles.yaml")

    with pytest.raises(ValueError, match="report-only"):
        build_universe_profile_split_worklist_plan(
            worklist=worklist,
            profiles=registry_path,
            output_dir=tmp_path / "plan",
            settings=UniverseProfileSplitWorklistPlanSettings(enable_universe_export=True),
        )


def test_outputs_have_no_trading_or_export_flags(tmp_path: Path) -> None:
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [_worklist_row("2024-04-02", "000001", "stock_core", "STOCK")],
    )
    registry_path = _write_registry(tmp_path / "profiles.yaml")

    result = build_universe_profile_split_worklist_plan(
        worklist=worklist,
        profiles=registry_path,
        output_dir=tmp_path / "plan",
    )
    row = result.plan_frame.iloc[0]

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
    assert row["plan_only"] == True  # noqa: E712
    assert result.audit_metadata["no_network_api"] is True
    assert result.audit_metadata["no_llm_api"] is True
    assert result.audit_metadata["no_cache_mutation"] is True


def test_cli_universe_profile_split_worklist_plan_works(tmp_path: Path, capsys) -> None:
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [
            _worklist_row("2024-04-02", "000001", "etf_core", "STOCK"),
            _worklist_row("2024-04-02", "510300", "etf_core", "ETF"),
        ],
    )
    registry_path = _write_registry(tmp_path / "profiles.yaml")
    policy = build_universe_profile_policy_audit(worklist=worklist, output_dir=tmp_path / "audit")

    code = cli.main(
        [
            "universe-profile-split-worklist-plan",
            "--worklist",
            str(worklist),
            "--policy-audit",
            str(policy.artifact_paths["audit_csv"]),
            "--profiles",
            str(registry_path),
            "--output-dir",
            str(tmp_path / "plan"),
        ]
    )

    output = capsys.readouterr()
    assert code == 0
    assert "row_count: 2" in output.out
    assert "recommended_stock_core_count: 1" in output.out
    assert "recommended_etf_core_count: 1" in output.out
    assert "No approval, rejection, active worklist mutation" in output.out


def _write_registry(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "profiles:",
                "  stock_core:",
                "    allowed_instrument_types: [STOCK]",
                "    profile_type: production_candidate",
                "    mixed_allowed: false",
                "    demo_only: false",
                "  etf_core:",
                "    allowed_instrument_types: [ETF]",
                "    profile_type: production_candidate",
                "    mixed_allowed: false",
                "    demo_only: false",
                "  mixed_demo_core:",
                "    allowed_instrument_types: [STOCK, ETF]",
                "    profile_type: demo_mixed",
                "    mixed_allowed: true",
                "    demo_only: true",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _write_worklist(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _worklist_row(signal_date: str, symbol: str, universe_name: str, instrument_type: str) -> dict:
    return {
        "worklist_id": "worklist001",
        "review_id": "review001",
        "signal_date": signal_date,
        "symbol": symbol,
        "universe_name": universe_name,
        "suggested_instrument_type": instrument_type,
        "current_review_status": "NEEDS_MANUAL_REVIEW",
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "worklist_only": True,
    }
