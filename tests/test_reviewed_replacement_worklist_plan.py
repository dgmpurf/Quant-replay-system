from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system import cli
from quant_replay_system.reviewed_replacement_worklist_plan import (
    ReviewedReplacementWorklistPlanSettings,
    build_reviewed_replacement_worklist_plan,
)
from quant_replay_system.universe_profile_policy_audit import build_universe_profile_policy_audit
from quant_replay_system.universe_profile_split_worklist_plan import build_universe_profile_split_worklist_plan


def test_replacement_plan_creates_profile_specific_templates_without_mutating_active_worklist(tmp_path: Path) -> None:
    split_plan = _build_split_plan(tmp_path)
    active_worklist = tmp_path / "worklist.csv"
    before = active_worklist.read_text(encoding="utf-8")

    result = build_reviewed_replacement_worklist_plan(
        split_plan=split_plan.artifact_paths["plan_csv"],
        output_dir=tmp_path / "replacement_plan",
    )

    assert active_worklist.read_text(encoding="utf-8") == before
    assert result.row_count == 3
    assert result.stock_core_row_count == 2
    assert result.etf_core_row_count == 1
    assert result.mixed_demo_core_row_count == 0
    assert set(result.plan_frame["future_universe_name"]) == {"stock_core", "etf_core"}
    assert set(result.plan_frame["review_status"]) == {"NEEDS_MANUAL_REVIEW"}
    assert result.audit_metadata["active_worklist_mutated"] is False
    assert result.audit_metadata["no_approval_applied"] is True
    assert result.audit_metadata["no_rejection_applied"] is True
    assert result.audit_metadata["no_universe_export"] is True

    stock_template = pd.read_csv(result.artifact_paths["replacement_update_template_stock_core"], dtype=str).fillna("")
    etf_template = pd.read_csv(result.artifact_paths["replacement_update_template_etf_core"], dtype=str).fillna("")
    mixed_template = pd.read_csv(result.artifact_paths["replacement_update_template_mixed_demo_core"], dtype=str).fillna("")
    assert len(stock_template) == 2
    assert len(etf_template) == 1
    assert len(mixed_template) == 0
    assert stock_template["symbol"].iloc[0] == "000001"
    assert "should_approve" not in result.plan_frame.columns


def test_replacement_plan_preserves_mixed_demo_rows_when_needed(tmp_path: Path) -> None:
    split_plan = _build_split_plan(tmp_path, include_unknown=True)

    result = build_reviewed_replacement_worklist_plan(
        split_plan=split_plan.artifact_paths["plan_csv"],
        output_dir=tmp_path / "replacement_plan",
    )

    assert result.mixed_demo_core_row_count == 1
    assert "mixed_demo_core" in set(result.plan_frame["future_universe_name"])


def test_replacement_plan_blocks_unsafe_settings(tmp_path: Path) -> None:
    split_plan = _build_split_plan(tmp_path)

    with pytest.raises(ValueError, match="report-only"):
        build_reviewed_replacement_worklist_plan(
            split_plan=split_plan.artifact_paths["plan_csv"],
            output_dir=tmp_path / "replacement_plan",
            settings=ReviewedReplacementWorklistPlanSettings(enable_approval=True),
        )


def test_cli_reviewed_replacement_worklist_plan_works(tmp_path: Path, capsys) -> None:
    split_plan = _build_split_plan(tmp_path)

    code = cli.main(
        [
            "reviewed-replacement-worklist-plan",
            "--split-plan",
            str(split_plan.artifact_paths["plan_csv"]),
            "--output-dir",
            str(tmp_path / "replacement_plan"),
        ]
    )

    output = capsys.readouterr().out
    assert code == 0
    assert "row_count: 3" in output
    assert "stock_core_row_count: 2" in output
    assert "etf_core_row_count: 1" in output
    assert "active_worklist_mutated: False" in output
    assert "No approval, rejection, active worklist mutation" in output


def _build_split_plan(tmp_path: Path, *, include_unknown: bool = False):
    rows = [
        _worklist_row("2024-04-02", "000001", "etf_core", "STOCK"),
        _worklist_row("2024-04-02", "000002", "etf_core", "STOCK"),
        _worklist_row("2024-04-02", "510300", "etf_core", "ETF"),
    ]
    if include_unknown:
        rows.append(_worklist_row("2024-04-02", "999999", "etf_core", "UNKNOWN"))
    worklist = _write_worklist(tmp_path / "worklist.csv", rows)
    registry = _write_registry(tmp_path / "profiles.yaml")
    policy = build_universe_profile_policy_audit(worklist=worklist, output_dir=tmp_path / "audit")
    return build_universe_profile_split_worklist_plan(
        worklist=worklist,
        policy_audit=policy.artifact_paths["audit_csv"],
        profiles=registry,
        output_dir=tmp_path / "split_plan",
    )


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
        "worklist_id": "1c7972988f59",
        "review_id": "7bc8ba08bf5a",
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
