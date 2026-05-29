import json
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system import cli
from quant_replay_system.point_in_time_universe_overlay_plan import OVERLAY_PLAN_COLUMNS
from quant_replay_system.point_in_time_universe_overlay_review import (
    build_pit_universe_overlay_review,
)


def test_template_only_mode_writes_review_template_without_approvals(tmp_path: Path) -> None:
    overlay_plan = _write_overlay_plan(tmp_path / "overlay_plan.csv")

    result = build_pit_universe_overlay_review(
        overlay_plan=overlay_plan,
        write_review_template_only=True,
        output_dir=tmp_path / "out",
    )

    assert result.row_count == 2
    assert result.approved_count == 0
    assert result.valid_for_signal_date_count == 0
    assert result.needs_manual_review_count == 2

    reviewed = pd.read_csv(result.artifact_paths["reviewed_overlay"], dtype={"symbol": str})
    assert reviewed["symbol"].tolist() == ["000001", "510300"]
    assert reviewed["review_status"].tolist() == ["NEEDS_MANUAL_REVIEW", "NEEDS_MANUAL_REVIEW"]
    assert reviewed["valid_for_signal_date"].eq(False).all()

    template = pd.read_csv(result.artifact_paths["review_template"], dtype={"symbol": str})
    assert "reviewer" in template.columns
    assert "evidence_source" in template.columns
    assert "survivorship_bias_resolved" in template.columns

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["current_candidates_executed"] is False
    assert metadata["snapshot_manifest_built"] is False
    assert metadata["forward_returns_computed"] is False
    assert metadata["cache_mutated"] is False
    assert metadata["network_api_called"] is False


def test_approved_row_becomes_valid_only_with_required_pit_evidence(tmp_path: Path) -> None:
    overlay_plan = _write_overlay_plan(tmp_path / "overlay_plan.csv")
    updates = _write_review_updates(
        tmp_path / "updates.csv",
        [
            _approved_update("000001"),
            _needs_more_evidence_update("510300"),
        ],
    )

    result = build_pit_universe_overlay_review(
        overlay_plan=overlay_plan,
        review_updates=updates,
        output_dir=tmp_path / "out",
    )

    assert result.approved_count == 1
    assert result.needs_more_evidence_count == 1
    assert result.valid_for_signal_date_count == 1

    rows = result.reviewed_frame.sort_values("symbol").reset_index(drop=True)
    approved = rows.loc[rows["symbol"] == "000001"].iloc[0]
    assert approved["review_status"] == "APPROVED_FOR_PIT_UNIVERSE"
    assert approved["valid_for_signal_date"] is True
    assert approved["include_flag"] is True
    assert approved["reviewer"] == "reviewer-a"
    assert approved["listed_date"] == "1991-04-03"
    assert approved["is_active"] is True
    assert approved["survivorship_bias_resolved"] is True
    assert approved["no_live_trading"] is True
    assert approved["no_broker_api"] is True
    assert approved["no_order_placement"] is True
    assert approved["no_message_sent"] is True
    assert approved["review_only"] is True


def test_approval_missing_reviewer_is_blocked_as_needs_more_evidence(tmp_path: Path) -> None:
    overlay_plan = _write_overlay_plan(tmp_path / "overlay_plan.csv")
    update = _approved_update("000001")
    update["reviewer"] = ""
    updates = _write_review_updates(tmp_path / "updates.csv", [update])

    result = build_pit_universe_overlay_review(
        overlay_plan=overlay_plan,
        review_updates=updates,
        output_dir=tmp_path / "out",
    )

    row = result.reviewed_frame.loc[result.reviewed_frame["symbol"] == "000001"].iloc[0]
    assert row["review_status"] == "NEEDS_MORE_EVIDENCE"
    assert row["valid_for_signal_date"] is False
    assert "reviewer" in row["blocker_reason"]
    assert result.approved_count == 0


def test_unresolved_survivorship_warning_blocks_approval(tmp_path: Path) -> None:
    overlay_plan = _write_overlay_plan(tmp_path / "overlay_plan.csv")
    update = _approved_update("000001")
    update["survivorship_bias_resolved"] = False
    updates = _write_review_updates(tmp_path / "updates.csv", [update])

    result = build_pit_universe_overlay_review(
        overlay_plan=overlay_plan,
        review_updates=updates,
        output_dir=tmp_path / "out",
    )

    row = result.reviewed_frame.loc[result.reviewed_frame["symbol"] == "000001"].iloc[0]
    assert row["review_status"] == "NEEDS_MORE_EVIDENCE"
    assert row["valid_for_signal_date"] is False
    assert "survivorship_bias_resolved" in row["blocker_reason"]


def test_delisted_before_signal_date_blocks_approval(tmp_path: Path) -> None:
    overlay_plan = _write_overlay_plan(tmp_path / "overlay_plan.csv")
    update = _approved_update("000001")
    update["delisted_date_evidence"] = "2024-03-29"
    updates = _write_review_updates(tmp_path / "updates.csv", [update])

    result = build_pit_universe_overlay_review(
        overlay_plan=overlay_plan,
        review_updates=updates,
        output_dir=tmp_path / "out",
    )

    row = result.reviewed_frame.loc[result.reviewed_frame["symbol"] == "000001"].iloc[0]
    assert row["review_status"] == "NEEDS_MORE_EVIDENCE"
    assert row["valid_for_signal_date"] is False
    assert "delisted_date" in row["blocker_reason"]


def test_invalid_review_status_is_rejected(tmp_path: Path) -> None:
    overlay_plan = _write_overlay_plan(tmp_path / "overlay_plan.csv")
    update = _approved_update("000001")
    update["review_status"] = "APPROVE_NOW"
    updates = _write_review_updates(tmp_path / "updates.csv", [update])

    with pytest.raises(ValueError, match="Invalid review_status"):
        build_pit_universe_overlay_review(
            overlay_plan=overlay_plan,
            review_updates=updates,
            output_dir=tmp_path / "out",
        )


def test_review_workflow_does_not_execute_candidates_snapshots_or_delivery(tmp_path: Path) -> None:
    overlay_plan = _write_overlay_plan(tmp_path / "overlay_plan.csv")
    updates = _write_review_updates(tmp_path / "updates.csv", [_approved_update("000001")])

    result = build_pit_universe_overlay_review(
        overlay_plan=overlay_plan,
        review_updates=updates,
        output_dir=tmp_path / "out",
    )

    assert result.audit_metadata["current_candidates_executed"] is False
    assert result.audit_metadata["snapshot_manifest_built"] is False
    assert result.audit_metadata["forward_returns_computed"] is False
    assert result.audit_metadata["data_pipeline_executed"] is False
    assert result.audit_metadata["cache_mutated"] is False
    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["order_placement_enabled"] is False
    assert result.audit_metadata["message_sent"] is False
    assert result.audit_metadata["network_api_called"] is False


def test_cli_pit_universe_overlay_review_template_only_works(tmp_path: Path, capsys) -> None:
    overlay_plan = _write_overlay_plan(tmp_path / "overlay_plan.csv")

    code = cli.main(
        [
            "pit-universe-overlay-review",
            "--overlay-plan",
            str(overlay_plan),
            "--write-review-template-only",
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "review_id:" in output.out
    assert "approved_count: 0" in output.out
    assert "needs_manual_review_count: 2" in output.out
    assert "valid_for_signal_date_count: 0" in output.out
    assert "No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM API, or external API was invoked." in output.out


def _write_overlay_plan(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            _overlay_row("000001"),
            _overlay_row("510300"),
        ],
        columns=OVERLAY_PLAN_COLUMNS,
    ).to_csv(path, index=False)
    return path


def _write_review_updates(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _overlay_row(symbol: str) -> dict:
    return {
        "overlay_plan_id": "plan001",
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "proposed_as_of_date": "2024-04-02",
        "proposed_available_time": "2024-04-02 08:00:00",
        "base_universe_path": "data/raw/LOCAL_CSV/universe_overlay/base/raw_data.csv",
        "base_universe_as_of_date": "2024-05-20",
        "base_universe_available_time": "2024-05-20 08:00:00",
        "include_flag": "",
        "review_status": "NEEDS_MANUAL_REVIEW",
        "review_reason": "Base universe is later than the signal date; manual review is required.",
        "source": "LOCAL_TEST",
        "upstream_source": "LOCAL_TEST",
        "survivorship_bias_warning": True,
        "manual_review_required": True,
        "valid_for_signal_date": False,
        "blocker_reason": "Universe as_of_date is later than signal date.",
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "plan_only": True,
    }


def _approved_update(symbol: str) -> dict:
    return {
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "include_flag": True,
        "review_status": "APPROVED_FOR_PIT_UNIVERSE",
        "reviewer": "reviewer-a",
        "reviewed_at": "2024-05-29T10:00:00+08:00",
        "review_reason": "Local PIT evidence reviewed.",
        "evidence_source": "LOCAL_REVIEW_FIXTURE",
        "evidence_path": "outputs/reports/manual_diagnostics/local_evidence.csv",
        "evidence_reference": "",
        "listed_date_evidence": "1991-04-03",
        "delisted_date_evidence": "",
        "is_active_evidence": True,
        "is_st": False,
        "is_suspended": False,
        "survivorship_bias_resolved": True,
    }


def _needs_more_evidence_update(symbol: str) -> dict:
    return {
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "include_flag": False,
        "review_status": "NEEDS_MORE_EVIDENCE",
        "reviewer": "reviewer-a",
        "reviewed_at": "2024-05-29T10:00:00+08:00",
        "review_reason": "Need a PIT ETF listing source.",
        "evidence_source": "",
        "evidence_path": "",
        "evidence_reference": "",
        "listed_date_evidence": "",
        "delisted_date_evidence": "",
        "is_active_evidence": "",
        "is_st": "",
        "is_suspended": "",
        "survivorship_bias_resolved": False,
    }
