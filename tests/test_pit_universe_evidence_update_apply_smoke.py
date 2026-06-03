from pathlib import Path

import pandas as pd

from quant_replay_system.point_in_time_universe_evidence_update_ingestion import (
    build_pit_universe_evidence_update_ingestion,
)
from quant_replay_system.point_in_time_universe_export_staging import (
    build_pit_universe_export_staging,
)
from quant_replay_system.point_in_time_universe_overlay_export_readiness import (
    build_pit_universe_overlay_export_readiness,
)
from quant_replay_system.point_in_time_universe_overlay_plan import OVERLAY_PLAN_COLUMNS
from quant_replay_system.point_in_time_universe_overlay_review import (
    build_pit_universe_overlay_review,
)


def test_fixture_backed_pit_universe_evidence_update_apply_smoke_remains_diagnostic_only(
    tmp_path: Path,
) -> None:
    """Prove clean reviewer updates can flow through the PIT review chain without active export."""

    diagnostic_root = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "pit_apply_smoke"
    symbols = ["000001", "000002", "159915", "510300"]
    completed_updates = _write_csv(
        tmp_path / "completed_updates.csv",
        [
            _complete_approved_update("000001"),
            _missing_evidence_update("000002"),
            _unresolved_survivorship_update("159915"),
            _future_available_time_update("510300"),
        ],
    )
    worklist = _write_csv(tmp_path / "worklist.csv", [_worklist_row(symbol) for symbol in symbols])
    overlay_plan = _write_csv(
        tmp_path / "overlay_plan.csv",
        [_overlay_plan_row(symbol) for symbol in symbols],
        columns=OVERLAY_PLAN_COLUMNS,
    )

    ingestion = build_pit_universe_evidence_update_ingestion(
        completed_updates=completed_updates,
        worklist=worklist,
        output_dir=diagnostic_root / "ingestion",
    )

    assert ingestion.row_count == 4
    assert ingestion.ready_for_review_update_count == 1
    assert ingestion.blocked_count == 3
    assert ingestion.approval_requested_count == 4
    assert ingestion.duplicate_identity_count == 0
    assert ingestion.suggested_copy_risk_count == 1
    assert ingestion.audit_metadata["approval_applied"] is False
    assert ingestion.audit_metadata["universe_exported"] is False
    assert ingestion.audit_metadata["would_write_data_raw"] is False
    assert ingestion.audit_metadata["would_write_data_processed"] is False
    assert ingestion.audit_metadata["no_current_candidates_generated"] is True
    assert ingestion.audit_metadata["no_snapshot_built"] is True
    assert ingestion.audit_metadata["no_forward_labels"] is True
    assert ingestion.audit_metadata["no_live_trading"] is True
    assert ingestion.audit_metadata["no_broker_api"] is True
    assert ingestion.audit_metadata["no_order_placement"] is True
    assert ingestion.audit_metadata["no_message_sent"] is True
    assert ingestion.audit_metadata["network_api_called"] is False
    assert ingestion.audit_metadata["llm_api_called"] is False

    clean_updates = pd.read_csv(ingestion.artifact_paths["review_updates"], dtype={"symbol": str})
    assert clean_updates["symbol"].tolist() == ["000001"]
    assert clean_updates["review_status"].tolist() == ["APPROVED_FOR_PIT_UNIVERSE"]
    assert clean_updates["symbol"].iloc[0] == "000001"
    assert "000002" not in clean_updates["symbol"].tolist()
    assert "159915" not in clean_updates["symbol"].tolist()
    assert "510300" not in clean_updates["symbol"].tolist()

    ingestion_by_symbol = ingestion.ingestion_frame.set_index("symbol")
    assert ingestion_by_symbol.loc["000002", "ingestion_status"] == "UPDATE_BLOCKED_SUGGESTED_HINT_COPY_RISK"
    assert ingestion_by_symbol.loc["000002", "suggested_copy_risk"] is True
    assert ingestion_by_symbol.loc["159915", "ingestion_status"] == "UPDATE_BLOCKED_UNRESOLVED_SURVIVORSHIP"
    assert ingestion_by_symbol.loc["510300", "ingestion_status"] == "UPDATE_BLOCKED_INVALID_PIT_DATES"

    review = build_pit_universe_overlay_review(
        overlay_plan=overlay_plan,
        review_updates=ingestion.artifact_paths["review_updates"],
        output_dir=diagnostic_root / "review",
    )

    assert review.approved_count == 1
    assert review.needs_more_evidence_count == 0
    assert review.valid_for_signal_date_count == 1
    reviewed_by_symbol = review.reviewed_frame.set_index("symbol")
    assert reviewed_by_symbol.loc["000001", "review_status"] == "APPROVED_FOR_PIT_UNIVERSE"
    assert reviewed_by_symbol.loc["000001", "valid_for_signal_date"] is True
    assert reviewed_by_symbol.loc["000002", "review_status"] == "NEEDS_MANUAL_REVIEW"
    assert review.audit_metadata["current_candidates_executed"] is False
    assert review.audit_metadata["snapshot_manifest_built"] is False
    assert review.audit_metadata["forward_returns_computed"] is False
    assert review.audit_metadata["network_api_called"] is False

    readiness = build_pit_universe_overlay_export_readiness(
        review=review.artifact_paths["reviewed_overlay"],
        output_dir=diagnostic_root / "export_readiness",
    )

    assert readiness.approved_count == 1
    assert readiness.export_ready_count == 1
    assert readiness.blocked_count > 0
    assert readiness.missing_required_columns_count == 3
    assert readiness.unresolved_survivorship_warning_count == 3
    readiness_by_symbol = readiness.readiness_frame.set_index("symbol")
    assert readiness_by_symbol.loc["000001", "export_ready"] is True
    assert readiness_by_symbol.loc["000001", "required_column_missing_count"] == 0
    assert readiness.audit_metadata["universe_exported"] is False
    assert readiness.audit_metadata["would_write_data_raw"] is False
    assert readiness.audit_metadata["would_write_data_processed"] is False
    assert readiness.audit_metadata["no_current_candidates_generated"] is True
    assert readiness.audit_metadata["no_snapshot_built"] is True
    assert readiness.audit_metadata["no_forward_labels"] is True
    assert readiness.audit_metadata["network_api_called"] is False
    assert readiness.audit_metadata["llm_api_called"] is False

    blocked_by_default = build_pit_universe_export_staging(
        export_readiness=readiness.artifact_paths["readiness_csv"],
        output_dir=diagnostic_root / "staging_blocked_by_default",
    )

    assert blocked_by_default.source_is_diagnostic is True
    assert blocked_by_default.staging_status == "EXPORT_STAGING_BLOCKED_DIAGNOSTIC_SOURCE"
    assert blocked_by_default.staged_row_count == 0

    staging = build_pit_universe_export_staging(
        export_readiness=readiness.artifact_paths["readiness_csv"],
        output_dir=diagnostic_root / "staging",
        allow_diagnostic_source=True,
    )

    assert staging.source_is_diagnostic is True
    assert staging.staging_status == "EXPORT_STAGING_DRY_RUN_CREATED"
    assert staging.staged_row_count == 1
    assert staging.blocked_count > 0
    assert staging.staged_universe_frame["symbol"].tolist() == ["000001"]
    assert staging.audit_metadata["active_staging_allowed"] is False
    assert staging.audit_metadata["would_write_data_raw"] is False
    assert staging.audit_metadata["would_write_data_processed"] is False
    assert staging.audit_metadata["no_current_candidates_generated"] is True
    assert staging.audit_metadata["no_snapshot_built"] is True
    assert staging.audit_metadata["no_forward_labels"] is True
    assert staging.audit_metadata["no_live_trading"] is True
    assert staging.audit_metadata["no_broker_api"] is True
    assert staging.audit_metadata["no_order_placement"] is True
    assert staging.audit_metadata["no_message_sent"] is True
    assert staging.audit_metadata["network_api_called"] is False
    assert staging.audit_metadata["llm_api_called"] is False

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()


def _write_csv(path: Path, rows: list[dict], *, columns: list[str] | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False)
    return path


def _complete_approved_update(symbol: str) -> dict:
    return {
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "review_status": "APPROVED_FOR_PIT_UNIVERSE",
        "include_flag": True,
        "reviewer": "synthetic_diagnostic",
        "reviewed_at": "2024-04-02 09:00:00",
        "review_reason": "diagnostic smoke only, not real PIT evidence",
        "evidence_source": "SYNTHETIC_DIAGNOSTIC",
        "evidence_path": "",
        "evidence_reference": "SYNTHETIC_LOCAL_TEST_ONLY",
        "listed_date": "1991-04-03",
        "delisted_date": "",
        "is_active": True,
        "is_st": False,
        "is_suspended": False,
        "listed_date_evidence": "1991-04-03",
        "delisted_date_evidence": "",
        "is_active_evidence": True,
        "survivorship_bias_resolved": True,
        "as_of_date": "2024-04-02",
        "name": f"Diagnostic {symbol}",
        "instrument_type": "ETF" if symbol.startswith(("15", "51")) else "STOCK",
        "exchange": "SZSE",
        "industry": "DIAGNOSTIC_UNKNOWN",
        "min_lot": "100",
        "t_plus_rule": "T+1",
        "available_time": "2024-04-02 08:00:00",
        "revision_id": f"synthetic-diagnostic-20240402-{symbol}",
        "source": "SYNTHETIC_DIAGNOSTIC",
    }


def _missing_evidence_update(symbol: str) -> dict:
    row = _complete_approved_update(symbol)
    row.update(
        {
            "reviewer": "",
            "evidence_reference": "",
            "listed_date_evidence": "",
            "is_active_evidence": "",
        }
    )
    return row


def _unresolved_survivorship_update(symbol: str) -> dict:
    row = _complete_approved_update(symbol)
    row["survivorship_bias_resolved"] = False
    return row


def _future_available_time_update(symbol: str) -> dict:
    row = _complete_approved_update(symbol)
    row["available_time"] = "2024-04-03 08:00:00"
    return row


def _overlay_plan_row(symbol: str) -> dict:
    return {
        "overlay_plan_id": "plan001",
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "proposed_as_of_date": "2024-04-02",
        "proposed_available_time": "2024-04-02 08:00:00",
        "base_universe_path": "data/raw/LOCAL_CSV/universe_overlay/future/raw_data.csv",
        "base_universe_as_of_date": "2024-05-20",
        "base_universe_available_time": "2024-05-20 08:00:00",
        "include_flag": False,
        "review_status": "NEEDS_MANUAL_REVIEW",
        "review_reason": "Base universe is later than the signal date.",
        "source": "LOCAL_CSV",
        "upstream_source": "SYNTHETIC_DIAGNOSTIC",
        "survivorship_bias_warning": True,
        "manual_review_required": True,
        "valid_for_signal_date": False,
        "blocker_reason": "Template row is not reviewed and is not valid for execution.",
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "plan_only": True,
    }


def _worklist_row(symbol: str) -> dict:
    return {
        "worklist_id": "worklist001",
        "review_id": "review001",
        "helper_id": "helper001",
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "current_review_status": "NEEDS_MANUAL_REVIEW",
        "current_valid_for_signal_date": False,
        "survivorship_bias_warning": True,
        "survivorship_bias_resolved": False,
        "suggested_name": "Suggested Name",
        "suggested_instrument_type": "STOCK",
        "suggested_exchange": "SZSE",
        "suggested_industry": "BANKING",
        "suggested_min_lot": "100",
        "suggested_t_plus_rule": "T+1",
        "suggested_is_active": True,
        "suggested_is_st": False,
        "suggested_is_suspended": False,
        "suggested_source": "LOCAL_HINT",
        "suggested_revision_id": "hint-v1",
        "hint_available_time": "2024-05-20 08:00:00",
        "hint_is_future_dated_for_signal_date": True,
        "hint_authoritative_for_pit": False,
        "missing_reviewer": True,
        "missing_reviewed_at": True,
        "missing_review_reason": False,
        "missing_evidence_source": True,
        "missing_evidence_path_or_reference": True,
        "missing_listed_date_evidence": True,
        "missing_is_active_evidence": True,
        "missing_survivorship_bias_resolution": True,
        "missing_required_universe_metadata": True,
        "required_next_evidence_fields": "reviewer,evidence_source",
        "suggested_next_review_action": "Collect PIT evidence.",
        "reviewer": "",
        "reviewed_at": "",
        "review_reason": "Manual review required.",
        "evidence_source": "",
        "evidence_path": "",
        "evidence_reference": "",
        "listed_date_evidence": "",
        "delisted_date_evidence": "",
        "is_active_evidence": "",
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "worklist_only": True,
    }
