import csv
import json
from pathlib import Path

import pytest

from quant_replay_system.historical_replay_official_status_evidence_packet_closure_worklist import (
    OUTPUT_FILES,
    RECOMMENDED_NEXT_TASK,
    REQUIRED_ROW_FIELDS,
    SAFETY_FALSE_FIELDS,
    STATUS_CREATED,
    WORKFLOW_STAGE,
    run_historical_replay_official_status_evidence_packet_closure_worklist,
)


EXPECTED_ROWS = {
    "000001": ("STOCK", "stock_core", "true"),
    "000002": ("STOCK", "stock_core", "true"),
    "159915": ("ETF", "etf_core", "false"),
    "300750": ("STOCK", "stock_core", "true"),
    "510300": ("ETF", "etf_core", "false"),
    "600000": ("STOCK", "stock_core", "true"),
    "600519": ("STOCK", "stock_core", "true"),
    "601318": ("STOCK", "stock_core", "true"),
    "688981": ("STOCK", "stock_core", "true"),
}
EXPECTED_NEXT_TASK = (
    "Historical Replay Official Source Hierarchy and Evidence Collection Planning for "
    "2024-04-02 etf_core Report-Only v0.1"
)


def test_default_run_creates_expected_report_only_artifacts(tmp_path: Path) -> None:
    result = run_historical_replay_official_status_evidence_packet_closure_worklist(
        root=tmp_path / "repo",
        output_dir=tmp_path / "out",
        run_id="unit_test_run",
    )

    assert result.status == STATUS_CREATED
    assert result.health_status == "WARN"
    assert result.workflow_stage == WORKFLOW_STAGE
    assert set(result.artifact_paths) == set(OUTPUT_FILES)
    for path in result.artifact_paths.values():
        assert path.exists()
        assert tmp_path / "out" in path.parents


def test_metadata_records_selected_sample_and_required_counts(tmp_path: Path) -> None:
    result = _run(tmp_path)
    metadata = _read_json(result.artifact_paths["metadata"])

    assert metadata["packet_worklist_run_id"] == "unit_test_run"
    assert metadata["signal_date"] == "2024-04-02"
    assert metadata["universe_name"] == "etf_core"
    assert metadata["status"] == STATUS_CREATED
    assert metadata["health_status"] == "WARN"
    assert metadata["workflow_stage"] == WORKFLOW_STAGE
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert metadata["local_only"] is True
    assert metadata["selected_sample_context_only"] is True
    assert metadata["row_count"] == 9
    assert metadata["stock_row_count"] == 7
    assert metadata["etf_row_count"] == 2
    assert metadata["blocked_count"] == 9
    assert metadata["missing_official_evidence_count"] == 9
    assert metadata["needs_manual_review_count"] == 9
    assert metadata["no_hit_review_needed_count"] == 9
    assert metadata["no_hit_accepted_context_count"] == 0
    assert metadata["packet_row_ready_not_pit_approved_count"] == 0
    assert metadata["profile_conflict_count"] == 7
    assert metadata["survivorship_warning_count"] == 9
    assert metadata["listed_status_missing_count"] == 9
    assert metadata["delisted_status_missing_count"] == 9
    assert metadata["st_status_missing_count"] == 7
    assert metadata["st_not_applicable_policy_missing_count"] == 2
    assert metadata["suspension_or_trading_status_missing_count"] == 9
    assert metadata["universe_membership_missing_count"] == 9
    assert metadata["source_id_missing_count"] == 9
    assert metadata["permission_class_missing_count"] == 9
    assert metadata["revision_id_missing_count"] == 9
    assert metadata["available_time_missing_count"] == 9
    assert RECOMMENDED_NEXT_TASK == EXPECTED_NEXT_TASK
    assert metadata["recommended_next_task"] == RECOMMENDED_NEXT_TASK


def test_generated_row_set_exactly_matches_selected_sample_and_preserves_symbols(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["worklist"])

    assert [row["symbol"] for row in rows] == list(EXPECTED_ROWS)
    for row in rows:
        expected_type, expected_profile, expected_conflict = EXPECTED_ROWS[row["symbol"]]
        assert row["signal_date"] == "2024-04-02"
        assert row["universe_name"] == "etf_core"
        assert row["legacy_universe_label"] == "etf_core"
        assert row["instrument_type"] == expected_type
        assert row["recommended_profile"] == expected_profile
        assert row["profile_conflict_flag"] == expected_conflict
        assert set(REQUIRED_ROW_FIELDS).issubset(row)


def test_all_rows_are_blocked_and_never_downstream_ready(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["worklist"])

    for row in rows:
        assert row["closure_status"] == "blocked"
        assert row["official_status_evidence_closed"] == "false"
        assert row["pit_admissibility_approved"] == "false"
        assert row["active_replay_input"] == "false"
        assert row["replay_execution_allowed"] == "false"
        assert row["buy_review_allowed"] == "false"
        assert row["trading_allowed"] == "false"
        assert row["no_hit_review_needed"] == "true"
        assert row["no_hit_acceptance_status"] != "no_hit_accepted_context"


def test_stock_rows_require_st_evidence_and_profile_conflict_review(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["worklist"])

    for row in rows:
        blockers = row["blocker_reason"].split(";")
        if row["instrument_type"] == "STOCK":
            assert "blocker_missing_st_status_evidence" in blockers
            assert "blocker_profile_conflict_unreviewed" in blockers
            assert row["st_status_evidence"] == "missing"
        else:
            assert "blocker_missing_st_status_evidence" not in blockers
            assert "blocker_profile_conflict_unreviewed" not in blockers


def test_etf_rows_require_st_not_applicable_policy(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["worklist"])

    for row in rows:
        blockers = row["blocker_reason"].split(";")
        if row["instrument_type"] == "ETF":
            assert "blocker_missing_st_not_applicable_policy" in blockers
            assert row["st_status_not_applicable_reason"] == "missing"
            assert row["st_policy_status"] == "missing_etf_not_applicable_policy"
        else:
            assert "blocker_missing_st_not_applicable_policy" not in blockers


@pytest.mark.parametrize(
    "blocker",
    [
        "blocker_missing_listed_status_evidence",
        "blocker_missing_delisted_status_evidence",
        "blocker_missing_suspension_or_trading_status",
        "blocker_missing_universe_membership_evidence",
        "blocker_universe_asof_after_signal",
        "blocker_missing_survivorship_rationale",
        "blocker_missing_source_id",
        "blocker_missing_raw_reference",
        "blocker_missing_revision_id",
        "blocker_missing_available_time",
    ],
)
def test_all_rows_have_required_common_blockers(tmp_path: Path, blocker: str) -> None:
    result = _run(tmp_path)
    rows = _read_csv(result.artifact_paths["worklist"])

    assert all(blocker in row["blocker_reason"].split(";") for row in rows)


def test_safety_flags_json_and_metadata_keep_all_downstream_flags_false(tmp_path: Path) -> None:
    result = _run(tmp_path)
    metadata = _read_json(result.artifact_paths["metadata"])
    safety = _read_json(result.artifact_paths["safety_flags"])

    for field in SAFETY_FALSE_FIELDS:
        assert metadata[field] is False
        assert safety[field] is False


def test_output_matrices_are_written_with_expected_content(tmp_path: Path) -> None:
    result = _run(tmp_path)

    family_rows = _read_csv(result.artifact_paths["evidence_family_matrix"])
    lineage_rows = _read_csv(result.artifact_paths["source_lineage_requirements"])
    blocker_rows = _read_csv(result.artifact_paths["blocker_matrix"])
    no_hit_rows = _read_csv(result.artifact_paths["no_hit_handoff_matrix"])

    assert {row["evidence_family"] for row in family_rows} >= {
        "listed_active_status",
        "delisted_not_delisted_status",
        "st_or_etf_not_applicable",
        "suspension_or_trading_status",
        "universe_membership",
        "survivorship_rationale",
    }
    assert {row["source_field"] for row in lineage_rows} >= {
        "source_id",
        "raw_reference",
        "permission_class",
        "revision_id",
        "available_time",
    }
    assert any(row["blocker_status"] == "blocker_missing_listed_status_evidence" for row in blocker_rows)
    assert len(no_hit_rows) == 9
    assert {row["no_hit_review_needed"] for row in no_hit_rows} == {"true"}


def test_report_states_packet_row_is_not_pit_or_replay_trading_readiness(tmp_path: Path) -> None:
    result = _run(tmp_path)
    report = result.artifact_paths["report"].read_text(encoding="utf-8")

    assert "packet row is not PIT approval" in report
    assert "not replay readiness" in report
    assert "not trading permission" in report
    assert EXPECTED_NEXT_TASK in report
    assert RECOMMENDED_NEXT_TASK in report


@pytest.mark.parametrize("blocked", ["data/raw", "data/processed", "data/cache", "docs/project_sources"])
def test_output_root_rejects_protected_paths(tmp_path: Path, blocked: str) -> None:
    with pytest.raises(ValueError, match="protected output path"):
        run_historical_replay_official_status_evidence_packet_closure_worklist(
            root=tmp_path / "repo",
            output_dir=Path(blocked),
        )


def test_no_docs_project_sources_or_protected_data_paths_are_created(tmp_path: Path) -> None:
    _run(tmp_path)

    assert not (tmp_path / "docs" / "project_sources").exists()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def _run(tmp_path: Path):
    return run_historical_replay_official_status_evidence_packet_closure_worklist(
        root=tmp_path / "repo",
        output_dir=tmp_path / "out",
        run_id="unit_test_run",
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
