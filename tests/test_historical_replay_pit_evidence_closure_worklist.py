import json
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.historical_replay_pit_evidence_closure_worklist import (
    RECOMMENDED_NEXT_TASK,
    REQUIRED_ROW_FIELDS,
    SAFETY_FALSE_FIELDS,
    STATUS_CREATED,
    STATUS_WARN_NO_CONTEXT,
    run_historical_replay_pit_evidence_closure_worklist,
)


def test_no_context_run_creates_safe_worklist_artifacts(tmp_path: Path) -> None:
    result = run_historical_replay_pit_evidence_closure_worklist(root=tmp_path / "reports", output_dir=tmp_path / "out")

    assert result.status == STATUS_WARN_NO_CONTEXT
    assert result.health_status == "WARN"
    assert result.row_count == 0
    assert result.artifact_paths["metadata"].exists()
    assert result.artifact_paths["worklist"].exists()
    assert result.artifact_paths["report"].exists()
    assert result.artifact_paths["summary"].exists()
    assert result.artifact_paths["blocker_summary"].exists()
    assert result.artifact_paths["safety_flags"].exists()


def test_no_context_run_never_marks_pit_evidence_closed(tmp_path: Path) -> None:
    result = run_historical_replay_pit_evidence_closure_worklist(root=tmp_path / "reports", output_dir=tmp_path / "out")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    safety = json.loads(result.artifact_paths["safety_flags"].read_text(encoding="utf-8"))

    assert metadata["pit_evidence_closed"] is False
    assert metadata["pit_admissibility_approved"] is False
    for field in SAFETY_FALSE_FIELDS:
        assert safety[field] is False
        assert metadata[field] is False


def test_overlay_fixture_rows_produce_selected_sample_worklist_rows(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["worklist"], dtype=str).fillna("")

    assert result.status == STATUS_CREATED
    assert rows["symbol"].tolist() == ["000001", "159915"]
    assert set(REQUIRED_ROW_FIELDS).issubset(rows.columns)
    assert set(rows["signal_date"]) == {"2024-04-02"}
    assert set(rows["universe_name"]) == {"etf_core"}


def test_leading_zero_symbols_remain_strings(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["worklist"], dtype={"symbol": str}).fillna("")

    assert rows.iloc[0]["symbol"] == "000001"


def test_mixed_stock_rows_under_etf_core_get_profile_conflict(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)
    _write_symbol_summary(root)

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["worklist"], dtype=str).fillna("")
    stock = rows.loc[rows["symbol"] == "000001"].iloc[0]

    assert stock["instrument_type"] == "STOCK"
    assert stock["profile_conflict_flag"] == "true"
    assert stock["recommended_profile"] == "stock_core"
    assert stock["profile_policy_status"] == "needs_review"


def test_etf_rows_still_require_source_and_timing_evidence(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)
    _write_symbol_summary(root)

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["worklist"], dtype=str).fillna("")
    etf = rows.loc[rows["symbol"] == "159915"].iloc[0]

    assert etf["instrument_type"] == "ETF"
    assert etf["profile_conflict_flag"] == "false"
    assert etf["source_id"] == "missing"
    assert etf["available_time"] == "2024-04-02 08:00:00"
    assert etf["available_time_timezone"] == "missing"
    assert etf["closure_status"] == "blocked"


def test_rows_with_universe_asof_after_signal_date_are_blocked(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)
    _write_execution_manifest(root)

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["worklist"], dtype=str).fillna("")

    assert set(rows["closure_status"]) == {"blocked"}
    assert rows["blocker_status"].str.contains("blocker_universe_asof_after_signal").all()


def test_rows_with_future_dated_hints_remain_blocked_or_needs_review(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)
    _write_date_summary(root)

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["worklist"], dtype=str).fillna("")

    assert set(rows["closure_status"]).issubset({"blocked", "needs_manual_review"})
    assert rows["blocker_status"].str.contains("blocker_future_dated_hint").all()


def test_rows_with_no_authoritative_hint_remain_blocked_or_needs_review(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)
    _write_date_summary(root)

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["worklist"], dtype=str).fillna("")

    assert set(rows["closure_status"]).issubset({"blocked", "needs_manual_review"})
    assert rows["blocker_status"].str.contains("blocker_missing_authoritative_hint").all()


def test_missing_source_id_creates_blocker_missing_source_id(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["worklist"], dtype=str).fillna("")

    assert rows["source_id"].eq("missing").all()
    assert rows["blocker_status"].str.contains("blocker_missing_source_id").all()


def test_missing_permission_class_blocks_closure_ready_status(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["worklist"], dtype=str).fillna("")

    assert rows["permission_class"].eq("missing").all()
    assert rows["closure_status"].ne("closure_ready_not_pit_approved").all()
    assert rows["blocker_status"].str.contains("blocker_missing_permission_class").all()


def test_missing_available_time_blocks_closure_ready_status(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root, proposed_available_time="")

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["worklist"], dtype=str).fillna("")

    assert rows["available_time"].eq("missing").all()
    assert rows["blocker_status"].str.contains("blocker_missing_available_time").all()


def test_available_time_after_decision_date_blocks_row(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root, proposed_available_time="2024-04-03 08:00:00")

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["worklist"], dtype=str).fillna("")

    assert rows["timing_relation_to_decision"].eq("after_decision").all()
    assert rows["blocker_status"].str.contains("blocker_available_time_after_decision").all()


def test_missing_survivorship_rationale_blocks_row(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["worklist"], dtype=str).fillna("")

    assert rows["survivorship_rationale"].eq("missing").all()
    assert rows["blocker_status"].str.contains("blocker_missing_survivorship_rationale").all()


def test_reviewer_no_hit_accepted_context_does_not_approve_pit(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)
    _write_no_hit_acceptance(root, accepted_count=2)

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["worklist"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert rows["no_hit_acceptance_status"].eq("no_hit_accepted_context").all()
    assert metadata["no_hit_accepted_context_count"] == 2
    assert metadata["pit_admissibility_approved"] is False


def test_closure_ready_not_pit_approved_does_not_set_pit_admissibility_approved(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root, include_closure_ready_context=True)

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["closure_ready_not_pit_approved_count"] == 0
    assert metadata["pit_admissibility_approved"] is False


def test_source_hash_preview_is_not_treated_as_validation(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root, source_hash_preview="abc123preview")

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["worklist"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert rows["source_hash_preview"].eq("abc123preview").all()
    assert metadata["source_hash_validated"] is False


def test_local_file_hash_preview_is_not_treated_as_pit_evidence(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root, local_file_hash_preview="localpreview")

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["worklist"], dtype=str).fillna("")

    assert rows["local_file_hash_preview"].eq("localpreview").all()
    assert rows["closure_status"].eq("blocked").all()


def test_all_required_safety_flags_remain_false(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    safety = json.loads(result.artifact_paths["safety_flags"].read_text(encoding="utf-8"))
    rows = pd.read_csv(result.artifact_paths["worklist"], dtype=str).fillna("")

    for field in SAFETY_FALSE_FIELDS:
        assert safety[field] is False
        assert result.metadata[field] is False
        assert rows[field].eq("false").all()


@pytest.mark.parametrize("blocked", ["data/raw", "data/processed", "data/cache", "docs/project_sources"])
def test_output_root_rejects_protected_paths(tmp_path: Path, blocked: str) -> None:
    with pytest.raises(ValueError, match="protected output path"):
        run_historical_replay_pit_evidence_closure_worklist(root=tmp_path / "reports", output_dir=Path(blocked))


def test_generated_report_contains_worklist_row_is_not_pit_approval(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    report = result.artifact_paths["report"].read_text(encoding="utf-8")

    assert "worklist row is not PIT approval" in report


def test_recommended_next_task_points_to_official_status_evidence_planning(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    report = result.artifact_paths["report"].read_text(encoding="utf-8")

    assert metadata["recommended_next_task"] == RECOMMENDED_NEXT_TASK
    assert RECOMMENDED_NEXT_TASK in report
    assert "Artifact Views / Status Planning" not in metadata["recommended_next_task"]
    assert "Research-Status Integration Planning" not in metadata["recommended_next_task"]


def test_generated_report_contains_no_replay_or_trading_readiness_wording(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)

    result = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    report = result.artifact_paths["report"].read_text(encoding="utf-8")

    assert "READY_FOR_REPLAY" not in report
    assert "BUY_REVIEW_READY" not in report
    assert "TRADING_READY" not in report


def test_no_protected_data_path_writes_are_performed(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)

    run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def _write_overlay(
    root: Path,
    *,
    proposed_available_time: str = "2024-04-02 08:00:00",
    source_hash_preview: str = "",
    local_file_hash_preview: str = "",
    include_closure_ready_context: bool = False,
) -> None:
    path = root / "point_in_time_universe_overlay_plan" / "38a254c54024"
    path.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "overlay_plan_id": "38a254c54024",
            "signal_date": "2024-04-02",
            "symbol": "000001",
            "universe_name": "etf_core",
            "proposed_as_of_date": "2024-04-02",
            "proposed_available_time": proposed_available_time,
            "base_universe_path": "data/raw/LOCAL_CSV/universe_overlay/raw_data.csv",
            "base_universe_as_of_date": "2024-05-20",
            "base_universe_available_time": "2024-05-20 08:00:00",
            "include_flag": "",
            "review_status": "NEEDS_MANUAL_REVIEW",
            "review_reason": "Base universe is later than the signal date; manual point-in-time review is required before inclusion.",
            "source": "AKSHARE_OPTIONAL",
            "upstream_source": "TENCENT_FOR_STOCKS;SINA_FOR_ETFS",
            "survivorship_bias_warning": "True",
            "manual_review_required": "True",
            "valid_for_signal_date": "False",
            "blocker_reason": "Universe as_of_date is later than signal date.",
            "source_hash_preview": source_hash_preview,
            "local_file_hash_preview": local_file_hash_preview,
            "closure_status": "closure_ready_not_pit_approved" if include_closure_ready_context else "",
        },
        {
            "overlay_plan_id": "38a254c54024",
            "signal_date": "2024-04-02",
            "symbol": "159915",
            "universe_name": "etf_core",
            "proposed_as_of_date": "2024-04-02",
            "proposed_available_time": proposed_available_time,
            "base_universe_path": "data/raw/LOCAL_CSV/universe_overlay/raw_data.csv",
            "base_universe_as_of_date": "2024-05-20",
            "base_universe_available_time": "2024-05-20 08:00:00",
            "include_flag": "",
            "review_status": "NEEDS_MANUAL_REVIEW",
            "review_reason": "Base universe is later than the signal date; manual point-in-time review is required before inclusion.",
            "source": "MANUAL_ETF_OVERLAY",
            "upstream_source": "TENCENT_FOR_STOCKS;SINA_FOR_ETFS",
            "survivorship_bias_warning": "True",
            "manual_review_required": "True",
            "valid_for_signal_date": "False",
            "blocker_reason": "Universe as_of_date is later than signal date.",
            "source_hash_preview": source_hash_preview,
            "local_file_hash_preview": local_file_hash_preview,
            "closure_status": "closure_ready_not_pit_approved" if include_closure_ready_context else "",
        },
    ]
    pd.DataFrame(rows).to_csv(path / "point_in_time_universe_overlay_plan.csv", index=False)


def _write_symbol_summary(root: Path) -> None:
    path = root / "point_in_time_universe_evidence_review_worklist" / "1c7972988f59"
    path.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "worklist_id": "1c7972988f59",
                "symbol": "000001",
                "universe_name": "etf_core",
                "first_signal_date": "2024-04-02",
                "needs_evidence_count": "8",
                "future_dated_hint_count": "8",
                "authoritative_hint_count": "0",
                "suggested_name": "Ping An Bank",
                "suggested_instrument_type": "STOCK",
                "suggested_exchange": "SZSE",
            },
            {
                "worklist_id": "1c7972988f59",
                "symbol": "159915",
                "universe_name": "etf_core",
                "first_signal_date": "2024-04-02",
                "needs_evidence_count": "8",
                "future_dated_hint_count": "8",
                "authoritative_hint_count": "0",
                "suggested_name": "ChiNext ETF",
                "suggested_instrument_type": "ETF",
                "suggested_exchange": "SZSE",
            },
        ]
    ).to_csv(path / "pit_universe_evidence_review_symbol_summary.csv", index=False)


def _write_date_summary(root: Path) -> None:
    path = root / "point_in_time_universe_evidence_review_worklist" / "1c7972988f59"
    path.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "worklist_id": "1c7972988f59",
                "signal_date": "2024-04-02",
                "universe_name": "etf_core",
                "row_count": "2",
                "symbol_count": "2",
                "needs_evidence_count": "2",
                "future_dated_hint_count": "2",
                "authoritative_hint_count": "0",
                "valid_for_signal_date_count": "0",
            }
        ]
    ).to_csv(path / "pit_universe_evidence_review_date_summary.csv", index=False)


def _write_execution_manifest(root: Path) -> None:
    path = root / "current_candidates_backfill_execution_manifest" / "f98279630ce6"
    path.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "execution_manifest_id": "f98279630ce6",
                "signal_date": "2024-04-02",
                "universe": "etf_core",
                "universe_as_of_date": "2024-05-20",
                "universe_valid_for_signal_date": "False",
                "readiness_status": "BLOCKED_UNIVERSE_AS_OF",
                "blocker_reason": "Universe as_of_date is later than signal date.",
            }
        ]
    ).to_csv(path / "current_candidates_backfill_execution_manifest.csv", index=False)


def _write_no_hit_acceptance(root: Path, *, accepted_count: int) -> None:
    path = root / "reviewer_no_hit_source_coverage_acceptance" / "2e05e4b74794"
    path.mkdir(parents=True, exist_ok=True)
    (path / "metadata.json").write_text(
        json.dumps({"accepted_count": accepted_count, "status": "WARN"}, indent=2),
        encoding="utf-8",
    )
